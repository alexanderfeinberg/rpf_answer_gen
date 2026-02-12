"""FastAPI entrypoint for the Document Ingestion API."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .doc_api import document_router
from .rfp_api import rfp_router
from .answer_api import answer_router
from answer_gen.exceptions import UserError
from contextlib import asynccontextmanager

from .deps import build_document_worker, build_question_worker
from .answer_deps import build_answer_worker, build_rfp_bulk_answer_worker


load_dotenv()

logger = logging.getLogger("doc_ingestion_api")
logging.basicConfig(level=logging.INFO)

# Ignore Hugging face logs unless > WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

DEFAULT_PORT = 9001
DEFAULT_HOST = "0.0.0.0"
DEFAULT_MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


class LimitUploadSize(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the configured upload limit."""

    def __init__(self, app: FastAPI, max_upload_size: int):
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_upload_size:
                max_mb = round(self.max_upload_size / 1024 / 1024, 2)
                return Response(
                    status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                    content=f"File too large. Maximum size is {max_mb}MB.",
                )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning(f'Pulling Huggingface embedding weights down, please wait a moment...')
    build_document_worker()
    build_question_worker()
    build_answer_worker()
    build_rfp_bulk_answer_worker()

    logger.warning('Completed pulling weights from Huggingface.')

    yield

def create_app() -> FastAPI:
    app = FastAPI(title="Document Ingestion API", version="0.1.0", lifespan=lifespan)
    max_upload_size = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(DEFAULT_MAX_UPLOAD_SIZE_BYTES)))
    app.add_middleware(LimitUploadSize, max_upload_size=max_upload_size)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info("%s %s", request.method, request.url.path)
        return await call_next(request)

    @app.exception_handler(UserError)
    async def user_error_handler(request: Request, exc: UserError):
        payload: Dict[str, Any] = {"error": str(exc)}
        return JSONResponse(status_code=404, content=payload)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        payload: Dict[str, Any] = {"error": exc.detail or "HTTP error"}
        return JSONResponse(status_code=exc.status_code, content=payload, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        payload: Dict[str, Any] = {"error": "Validation failed", "details": exc.errors()}
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled server error")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

    app.include_router(document_router)
    app.include_router(rfp_router)
    app.include_router(answer_router)
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", str(DEFAULT_PORT)))
    print(f"Running Document Ingestion API server on {DEFAULT_HOST}:{port}.")
    uvicorn.run(app, host=DEFAULT_HOST, port=port)
