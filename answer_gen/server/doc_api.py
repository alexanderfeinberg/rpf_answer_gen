from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from answer_gen.exceptions import UserError
from answer_gen.utils.file_utils import is_pdf
from answer_gen.utils.config.config_utils import get_config_int

from answer_gen.exceptions import BulkUploadFailed

from .deps import get_document_worker

document_router = APIRouter(prefix="/api/documents")

@document_router.post("/upload")
async def upload_document(documents: list[UploadFile] = File(...)):
    payload: list[tuple[str, bytes]] = []
    worker = get_document_worker()

    max_documents = get_config_int("documents", "max_document_batch", fallback = 10)
    total_docs = len(documents)

    if total_docs > max_documents:
        raise BulkUploadFailed(f'Too many documents uploaded. Please upload under {str(max_documents)} documents')

    for f in documents:
        try:
            payload.append((f.filename or "document.pdf", await f.read()))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to read upload.")

    if not all((is_pdf(f[1]) for f in payload)):
        raise HTTPException(status_code=400, detail="Please ensure uploaded files are valid PDF's.")

    inserted_ids, failed = await worker(payload)

    return {"inserted_document_ids": inserted_ids, "failed" : failed}
