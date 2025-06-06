"""Grok API client with enterprise features."""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, List, Optional, Any
from datetime import datetime
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import (
    GROK_API_KEY, GROK_API_BASE, GROK_MODEL,
    GROK_TEMPERATURE, GROK_MAX_TOKENS, GROK_STREAMING
)
from .analytics import track_api_usage

logger = logging.getLogger("chaxai.grok")


class GrokClient:
    """Enterprise-grade Grok API client with streaming support."""
    
    def __init__(
        self,
        api_key: str = GROK_API_KEY,
        base_url: str = GROK_API_BASE,
        model: str = GROK_MODEL,
        timeout: float = 30.0
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = GROK_TEMPERATURE,
        max_tokens: int = GROK_MAX_TOKENS,
        stream: bool = GROK_STREAMING,
        tools: Optional[List[Dict]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a chat completion with Grok."""
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        try:
            start_time = datetime.utcnow()
            
            if stream:
                return await self._stream_chat_completion(payload, metadata)
            else:
                response = await self.client.post(
                    "/chat/completions",
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Track usage
                if metadata:
                    await track_api_usage(
                        model=self.model,
                        tokens_used=result.get("usage", {}).get("total_tokens", 0),
                        latency=(datetime.utcnow() - start_time).total_seconds(),
                        tenant_id=metadata.get("tenant_id"),
                        user_id=metadata.get("user_id")
                    )
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"Grok API error: {e}")
            raise
    
    async def _stream_chat_completion(
        self,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion responses."""
        
        start_time = datetime.utcnow()
        total_tokens = 0
        
        try:
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                                content = chunk["choices"][0]["delta"]["content"]
                                yield content
                                
                                # Estimate tokens (rough approximation)
                                total_tokens += len(content.split())
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse SSE data: {data}")
                
                # Track usage for streaming
                if metadata:
                    await track_api_usage(
                        model=self.model,
                        tokens_used=total_tokens * 1.3,  # Rough token estimate
                        latency=(datetime.utcnow() - start_time).total_seconds(),
                        tenant_id=metadata.get("tenant_id"),
                        user_id=metadata.get("user_id")
                    )
                    
        except httpx.HTTPError as e:
            logger.error(f"Grok streaming error: {e}")
            raise
    
    async def create_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ) -> List[float]:
        """Create embeddings using OpenAI until Grok supports embeddings."""
        # Note: This is a placeholder. When Grok releases embedding models,
        # update this to use Grok's API instead
        import openai
        from .config import OPENAI_API_KEY
        
        openai.api_key = OPENAI_API_KEY
        response = await openai.Embedding.acreate(
            model=model,
            input=text
        )
        return response["data"][0]["embedding"]
    
    async def function_calling(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        function_call: str = "auto"
    ) -> Dict[str, Any]:
        """Use Grok's function calling capability."""
        
        tools = [
            {
                "type": "function",
                "function": func
            }
            for func in functions
        ]
        
        response = await self.create_chat_completion(
            messages=messages,
            tools=tools,
            stream=False
        )
        
        return response


# Global client instance
grok_client = None

def get_grok_client() -> GrokClient:
    """Get or create Grok client singleton."""
    global grok_client
    if grok_client is None:
        grok_client = GrokClient()
    return grok_client