"""Enhanced vector store with Grok integration and advanced RAG."""

import os
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import asyncio
from functools import lru_cache

import numpy as np
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .config import (
    VECTOR_DIR, CACHE_DIR, EMBEDDING_MODEL,
    OPENAI_API_KEY, get_encryption_cipher
)
from .grok_client import get_grok_client
from .schemas import Question, Answer, DocumentInfo

logger = logging.getLogger("chaxai.vector")


class EnhancedVectorStore:
    """Advanced vector store with caching and metadata."""
    
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.vector_dir = Path(VECTOR_DIR) / tenant_id
        self.cache_dir = Path(CACHE_DIR) / tenant_id
        self.embeddings = self._get_embeddings()
        self.store = None
        self.metadata_store = {}
        self._load_metadata()
    
    @lru_cache(maxsize=1)
    def _get_embeddings(self):
        """Get embedding model (cached)."""
        return OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model=EMBEDDING_MODEL
        )
    
    def _load_metadata(self):
        """Load document metadata from encrypted store."""
        metadata_file = self.vector_dir / "metadata.enc"
        if metadata_file.exists():
            cipher = get_encryption_cipher()
            with open(metadata_file, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = cipher.decrypt(encrypted_data)
            self.metadata_store = json.loads(decrypted_data)
    
    def _save_metadata(self):
        """Save document metadata to encrypted store."""
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = self.vector_dir / "metadata.enc"
        cipher = get_encryption_cipher()
        data = json.dumps(self.metadata_store).encode()
        encrypted_data = cipher.encrypt(data)
        with open(metadata_file, "wb") as f:
            f.write(encrypted_data)
    
    async def load_store(self):
        """Load or create vector store."""
        if self.store is None:
            if self.vector_dir.exists():
                logger.info(f"Loading vector store for tenant {self.tenant_id}")
                self.store = FAISS.load_local(
                    str(self.vector_dir),
                    self.embeddings
                )
            else:
                logger.info(f"Creating new vector store for tenant {self.tenant_id}")
                self.store = FAISS.from_texts(
                    ["Initial document"],
                    self.embeddings,
                    metadatas=[{"source": "system", "tenant_id": self.tenant_id}]
                )
    
    async def add_documents(
        self,
        documents: List[Document],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add documents with enhanced metadata."""
        await self.load_store()
        
        # Enhance documents with metadata
        for doc in documents:
            doc_id = f"{self.tenant_id}_{datetime.utcnow().isoformat()}_{hash(doc.page_content)}"
            
            # Extract additional metadata
            doc.metadata.update({
                "tenant_id": self.tenant_id,
                "doc_id": doc_id,
                "indexed_at": datetime.utcnow().isoformat(),
                "char_count": len(doc.page_content),
                "word_count": len(doc.page_content.split()),
            })
            
            if metadata:
                doc.metadata.update(metadata)
            
            # Store extended metadata
            self.metadata_store[doc_id] = {
                "content_preview": doc.page_content[:200],
                "metadata": doc.metadata,
                "embeddings_model": EMBEDDING_MODEL,
            }
        
        # Add to vector store
        self.store.add_documents(documents)
        
        # Save everything
        self.store.save_local(str(self.vector_dir))
        self._save_metadata()
        
        logger.info(f"Added {len(documents)} documents for tenant {self.tenant_id}")
    
    async def hybrid_search(
        self,
        query: str,
        k: int = 4,
        rerank: bool = True
    ) -> List[Tuple[Document, float]]:
        """Hybrid search with semantic and keyword matching."""
        await self.load_store()
        
        # Semantic search
        semantic_results = self.store.similarity_search_with_score(query, k=k*2)
        
        # Keyword search (simple BM25-like scoring)
        query_terms = set(query.lower().split())
        keyword_scores = []
        
        for doc, semantic_score in semantic_results:
            content_terms = set(doc.page_content.lower().split())
            keyword_score = len(query_terms.intersection(content_terms)) / len(query_terms)
            
            # Combine scores (weighted)
            combined_score = 0.7 * (1 - semantic_score) + 0.3 * keyword_score
            keyword_scores.append((doc, combined_score))
        
        # Sort by combined score
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Rerank using Grok if enabled
        if rerank and len(keyword_scores) > 0:
            reranked = await self._rerank_with_grok(query, keyword_scores[:k*2])
            return reranked[:k]
        
        return keyword_scores[:k]
    
    async def _rerank_with_grok(
        self,
        query: str,
        results: List[Tuple[Document, float]]
    ) -> List[Tuple[Document, float]]:
        """Rerank results using Grok for better relevance."""
        client = get_grok_client()
        
        # Prepare reranking prompt
        passages = []
        for i, (doc, score) in enumerate(results):
            passages.append(f"Passage {i+1}: {doc.page_content[:500]}...")
        
        messages = [
            {
                "role": "system",
                "content": "You are a search result reranker. Given a query and passages, rank them by relevance. Return only the passage numbers in order of relevance, separated by commas."
            },
            {
                "role": "user",
                "content": f"Query: {query}\n\n" + "\n\n".join(passages) + "\n\nRank the passages by relevance (most relevant first):"
            }
        ]
        
        try:
            response = await client.create_chat_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=50,
                stream=False
            )
            
            # Parse ranking
            ranking_text = response["choices"][0]["message"]["content"]
            rankings = [int(x.strip()) - 1 for x in ranking_text.split(",") if x.strip().isdigit()]
            
            # Reorder results
            reranked = []
            for idx in rankings:
                if 0 <= idx < len(results):
                    reranked.append(results[idx])
            
            # Add any missing results
            for i, result in enumerate(results):
                if i not in rankings:
                    reranked.append(result)
            
            return reranked
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results


class VectorStoreManager:
    """Manage multiple tenant vector stores."""
    
    def __init__(self):
        self.stores: Dict[str, EnhancedVectorStore] = {}
    
    def get_store(self, tenant_id: str) -> EnhancedVectorStore:
        """Get or create vector store for tenant."""
        if tenant_id not in self.stores:
            self.stores[tenant_id] = EnhancedVectorStore(tenant_id)
        return self.stores[tenant_id]
    
    async def ask_question(
        self,
        question: Question,
        tenant_id: str = "default",
        user_id: Optional[str] = None
    ) -> Answer:
        """Ask a question using Grok with RAG."""
        store = self.get_store(tenant_id)
        
        # Search for relevant documents
        results = await store.hybrid_search(question.question, k=4)
        
        if not results:
            return Answer(
                answer="I couldn't find any relevant information in the knowledge base.",
                sources=[],
                confidence=0.0
            )
        
        # Prepare context
        context_parts = []
        sources = []
        
        for doc, score in results:
            context_parts.append(f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}")
            sources.append({
                "source": doc.metadata.get("source", "Unknown"),
                "score": float(score),
                "preview": doc.page_content[:100] + "..."
            })
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Build messages for Grok
        messages = [
            {
                "role": "system",
                "content": (
                    "You are ChaxAI, an enterprise-grade AI assistant. "
                    "Answer questions based on the provided context. "
                    "Be accurate, helpful, and cite your sources when possible. "
                    "If you're not sure about something, say so."
                )
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question.question}"
            }
        ]
        
        # Get answer from Grok
        client = get_grok_client()
        
        try:
            if GROK_STREAMING:
                # Stream the response
                full_response = ""
                async for chunk in await client.create_chat_completion(
                    messages=messages,
                    stream=True,
                    metadata={
                        "tenant_id": tenant_id,
                        "user_id": user_id
                    }
                ):
                    full_response += chunk
                
                answer_text = full_response
            else:
                # Non-streaming response
                response = await client.create_chat_completion(
                    messages=messages,
                    stream=False,
                    metadata={
                        "tenant_id": tenant_id,
                        "user_id": user_id
                    }
                )
                answer_text = response["choices"][0]["message"]["content"]
            
            # Calculate confidence based on source scores
            avg_score = sum(score for _, score in results) / len(results)
            confidence = min(avg_score * 100, 100)
            
            return Answer(
                answer=answer_text,
                sources=[s["source"] for s in sources],
                source_details=sources,
                confidence=confidence,
                model_used=client.model
            )
            
        except Exception as e:
            logger.error(f"Error getting answer from Grok: {e}")
            return Answer(
                answer="I encountered an error while processing your question. Please try again.",
                sources=[],
                confidence=0.0
            )


# Global manager instance
vector_manager = VectorStoreManager()