from answer_gen.utils.config.answer_worker_config import AnswerWorkerConfig, BulkAnswerWorkerConfig
from answer_gen.utils.config.config_utils import read_config
from answer_gen.components.answers.answer_worker import AnswerWorker
from answer_gen.components.answers.rfp_answer_worker import RfpBulkAnswerWorker
from answer_gen.utils.generative.clients.openai_client import OpenAIClient
from dotenv import load_dotenv
import os

load_dotenv()

ANSWER_WORKER = None
RFP_BULK_ANSWER_WORKER = None


def build_answer_worker():
    """Initialize and cache the singleton single-answer worker."""
    global ANSWER_WORKER
    config_path = os.getenv("CONFIG_FILE", "config/global.ini")
    db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL")

    if not db_url:
        raise RuntimeError("DB_URL or DATABASE_URL must be set")

    read_config(config_path)
    cfg = AnswerWorkerConfig.from_config()

    ANSWER_WORKER = AnswerWorker(
        db_url=db_url,
        generative_client=OpenAIClient(os.getenv("LLM_API_KEY")),
        config = cfg
    )


def build_rfp_bulk_answer_worker():
    """Initialize and cache the singleton bulk-answer worker."""
    global RFP_BULK_ANSWER_WORKER
    config_path = os.getenv("CONFIG_FILE", "config/global.ini")
    db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DB_URL or DATABASE_URL must be set")

    read_config(config_path)
    cfg = BulkAnswerWorkerConfig.from_config()
    gen_client = OpenAIClient(os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))

    RFP_BULK_ANSWER_WORKER = RfpBulkAnswerWorker(
        db_url=db_url,
        config=cfg,
        generative_client=gen_client,
    )


def get_answer_worker():
    """Return the single-answer worker, building it on first access."""
    if ANSWER_WORKER is None:
        build_answer_worker()
    return ANSWER_WORKER


def get_rfp_bulk_answer_worker():
    """Return the bulk-answer worker, building it on first access."""
    if RFP_BULK_ANSWER_WORKER is None:
        build_rfp_bulk_answer_worker()
    return RFP_BULK_ANSWER_WORKER
