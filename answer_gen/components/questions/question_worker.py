from __future__ import annotations

import logging
from answer_gen.utils.config.question_worker_config import QuestionWorkerConfig

from answer_gen.utils.document_utils import get_document_hash
from answer_gen.storage.db import build_bulk_connection
from answer_gen.storage.factories import rfp_factory
from answer_gen.storage import RFP, Question
from answer_gen.storage.persistence import Persistence

from answer_gen.utils.generative import generate_questions
from answer_gen.exceptions import EmptyRFP
from answer_gen.utils.generative.mappers import map_questions

logger = logging.getLogger(__name__)


class QuestionWorker:
    def __init__(self, db_url: str, generative_text_client, config: QuestionWorkerConfig):
        """Create a worker to parse and persist RFP questions via an LLM."""
        self._db_url = db_url
        self._gen_txt_client = generative_text_client
        self._config = config

    async def __call__(self, filename, rfp_content : bytes):
        """Upsert an RFP and (re)parse its questions; returns the RFP id."""
        with build_bulk_connection(self._db_url) as session:
            # Use one session for the full parse/update transaction.
            store = Persistence(session)
            rfp_hash = get_document_hash(rfp_content)

            rfp, do_parse = self._does_rfp_need_parsing(store, filename, rfp_hash)

            if rfp is None:
                rfp = self._insert_rfp(store, filename, filename, rfp_hash)

            if not do_parse:
                return {"rfp_id" : rfp.id, "questions" : []}

            try:
                questions = await generate_questions(
                    self._gen_txt_client,
                    self._config.prompt_path,
                    self._config.model,
                    rfp_content,
                )
            except Exception:
                logger.exception(
                    "Question generation failed filename=%s rfp_id=%s model=%s",
                    filename,
                    rfp.id,
                    self._config.model,
                )
                raise

            if len(questions) < 1:
                logger.warning(f'No questions extracted from RFP {filename}')
                raise EmptyRFP(f'No valid questions were found in the given RFP.')

            total_q = len(questions)
            logger.info("Parsed questions from RFP filename=%s total=%s", filename, total_q)

            normalized = [q.strip() for q in questions if q and q.strip()]
            new_set = set(normalized)

            # Compare latest parsed set against current DB state.
            existing, existing_set = self._get_existing_questions(store, rfp.id)
            if len(existing_set) > 0:
                self._delete_rfp_questions(store, rfp.id, new_set)

            # Refresh existing questions in case some were deleted
            existing, existing_set = self._get_existing_questions(store, rfp.id)

            to_insert: list[str] = sorted(list(new_set - existing_set))

            if to_insert:
                # Insert only questions that are newly introduced.
                question_models = map_questions(to_insert, rfp.id)
                store.bulk_insert_questions(question_models)
                store.commit()
                existing.extend(question_models)
                logger.info("Inserted new questions rfp_id=%s inserted=%s", rfp.id, len(question_models))

            return {"rfp_id" : rfp.id, "questions" : [q.id for q in existing]}

    def _does_rfp_need_parsing(self, store : Persistence, filename, rfp_hash):
        """Return `(rfp, should_parse)` based on hash lookup and document freshness."""
        rfp: RFP | None = store.get_rfp_by_hash(rfp_hash)

        if rfp is None:
            return None, True

        # Re-parse only when RFP is new or documents changed after last upload.
        most_rec_doc = store.get_most_recent_document()
        needs_q_parsing : bool = most_rec_doc is None or most_rec_doc.uploaded_at > rfp.uploaded_at

        if not needs_q_parsing:
            logger.info("RFP does not require re-parse filename=%s rfp_id=%s", filename, rfp.id)
            return rfp, False

        return rfp, True

    def _get_existing_questions(self, store : Persistence, rfp_id):
            """Fetch current questions for an RFP and return both list and text set."""
            existing = store.get_questions_by_rfp(rfp_id)
            return existing, {q.content for q in existing}

    def _delete_rfp_questions(self, store : Persistence, rfp_id, new_questions):
        """Delete persisted questions not present in the latest parsed question set."""
        # Delete questions that no longer exist in the latest parse.
        delete_count = str(len(new_questions))

        logger.info(f'Deleting {delete_count} associated with {str(rfp_id)}')
        store.delete_questions_not_in(rfp_id, list(new_questions))
        store.commit()

    def _insert_rfp(self, store : Persistence, filename : str, storage_url : str,  doc_hash : str) -> RFP:
        """Insert a new RFP row and return it with its id populated."""
        rfp = rfp_factory(
            filename, storage_url, doc_hash
        )
        store.insert_rfp(rfp)
        store.flush()
        store.commit()
        return rfp
