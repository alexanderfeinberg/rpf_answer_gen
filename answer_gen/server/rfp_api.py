from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, Body
from answer_gen.exceptions import UserError
from answer_gen.utils.file_utils import is_pdf

from .deps import get_question_worker

rfp_router = APIRouter(prefix="/api/rfp")

@rfp_router.post("/upload")
async def upload_rfp(rfp: UploadFile = File(...)):
    worker = get_question_worker()

    try:
        content = await rfp.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read upload: {exc}")

    if not is_pdf(content):
        raise HTTPException(status_code=400, detail="Please ensure uploaded files are valid PDF's.")

    result = await worker(rfp.filename or "rfp.pdf", content)
    return {**result}
