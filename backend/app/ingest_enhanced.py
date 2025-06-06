import asyncio
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile
from langchain.docstore.document import Document

from .config import DOCS_DIR, MAX_UPLOAD_MB
from .utils import secure_filename
from .vector_enhanced import vector_manager


class IngestManager:
    """Simple document ingestion manager."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self.docs_dir = Path(DOCS_DIR) / tenant_id
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    async def validate_file(self, file: UploadFile) -> UploadFile:
        ext = Path(file.filename).suffix.lower()
        if ext not in {".txt", ".md", ".pdf"}:
            raise ValueError("Unsupported file type")
        data = await file.read()
        if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
            raise ValueError("File too large")
        await file.seek(0)
        return file

    async def queue_ingestion(self, files: List[UploadFile], user_id: Optional[str] = None) -> str:
        task_id = uuid.uuid4().hex
        for upload in files:
            secure_name = secure_filename(upload.filename)
            dest = self.docs_dir / secure_name
            content = await upload.read()
            with open(dest, "wb") as f:
                f.write(content)
            await upload.seek(0)
            text = await self._extract_text(dest)
            document = Document(page_content=text, metadata={"source": secure_name, "tenant_id": self.tenant_id})
            await vector_manager.get_store(self.tenant_id).add_documents([document])
        return task_id

    async def process_queue(self) -> None:
        # In this simplified version ingestion happens immediately
        return

    async def _extract_text(self, path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        return path.read_text(encoding="utf-8", errors="ignore")
