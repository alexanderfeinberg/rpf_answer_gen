from answer_gen.utils.config.document_ingestor_config import DocumentIngestorConfig
from answer_gen.utils.config.question_worker_config import QuestionWorkerConfig
from answer_gen.utils.generative.clients.openai_client import OpenAIClient

from answer_gen.utils.config.config_utils import read_config
from answer_gen.components.ingestion.document_ingestor import DocumentIngestorWorker
from answer_gen.components.questions.question_worker import QuestionWorker
from dotenv import load_dotenv
import os

load_dotenv()

DOCUMENT_WORKER = None
QUESTION_WORKER = None

def build_document_worker():
    """Initialize and cache the singleton document ingestion worker."""
    global DOCUMENT_WORKER
    config_path = os.getenv("CONFIG_FILE", "config/global.ini")
    db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL")

    if not db_url:
        raise RuntimeError("DB_URL or DATABASE_URL must be set")

    read_config(config_path)
    cfg = DocumentIngestorConfig.from_config()

    DOCUMENT_WORKER = DocumentIngestorWorker(
        db_url=db_url,
        config = cfg
    )

def get_document_worker():
    """Return the document ingestion worker, building it on first access."""
    global DOCUMENT_WORKER
    if DOCUMENT_WORKER is None:
        build_document_worker()
    return DOCUMENT_WORKER


def build_question_worker():
    """Initialize and cache the singleton question parsing worker."""
    global QUESTION_WORKER
    config_path = os.getenv("CONFIG_FILE", "config/global.ini")
    db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL")

    if not db_url:
        raise RuntimeError("DB_URL or DATABASE_URL must be set")

    read_config(config_path)
    cfg = QuestionWorkerConfig.from_config()

    QUESTION_WORKER = QuestionWorker(
        db_url=db_url,
        generative_text_client=OpenAIClient(os.getenv("LLM_API_KEY")),
        config = cfg
    )

def get_question_worker():
    """Return the question worker, building it on first access."""
    if QUESTION_WORKER is None:
        build_question_worker()
    return QUESTION_WORKER
