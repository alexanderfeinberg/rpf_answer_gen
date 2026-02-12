from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, HTTPException, Body
from answer_gen.exceptions import UserError

from .models import BulkAnswerRequest, SingleAnswerRequest
from .answer_deps import (
    get_answer_worker,
    get_rfp_bulk_answer_worker,
)

answer_router = APIRouter(prefix="/api/answers")

@answer_router.post("/bulk-generate")
async def generate_bulk_answers(bulk_request: Annotated[BulkAnswerRequest, Body(embed=False)]):
    worker = get_rfp_bulk_answer_worker()
    result = await worker(bulk_request.rfp_id)

    return result

@answer_router.post("/generate")
async def generate_single_answer(single_request : Annotated[SingleAnswerRequest, Body(embed=False)]):
    worker = get_answer_worker()
    result = await worker(single_request.question_id)

    return result

@answer_router.get("/{answer_id}")
async def get_answer(answer_id : int):
    worker = get_answer_worker()
    resp = worker.fetch_answer(answer_id)

    return resp
