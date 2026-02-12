from __future__ import annotations

import logging
from typing import List
import json

from answer_gen.storage.db import build_connection
from answer_gen.storage.persistence import Persistence
from answer_gen.storage import Answer, Question
from answer_gen.utils.embedder import Embedder
from answer_gen.utils.generative import generate_answers
from answer_gen.utils.generative.mappers import map_answers
from answer_gen.utils.config.answer_worker_config import BulkAnswerWorkerConfig

from answer_gen.exceptions import DatabaseQueryError

logger = logging.getLogger(__name__)

class RfpBulkAnswerWorker:
    """Generate answers for all questions of an RFP, skipping those already answered."""

    def __init__(
        self,
        db_url: str,
        config: BulkAnswerWorkerConfig,
        generative_client,
    ):
        """Initialize bulk-answer generation dependencies and configuration."""
        self._db_url = db_url
        self._config = config
        self._generative_client = generative_client
        self._embedder = Embedder(config.embedding_model, batch_size = config.embedding_batch_size)
        self._answer_version_id = None

    async def __call__(self, rfp_id: int):
        """Generate missing answers for all questions under an RFP and return grouped results."""
        with build_connection(self._db_url) as session:
            # Load all questions once, including existing answers.
            store = Persistence(session)
            questions: List[Question] = store.get_questions_with_answers(rfp_id)

            already_answered = [q for q in questions if q.answers]
            to_answer = [q for q in questions if not q.answers]
            logger.info(
                "Processing bulk answers rfp_id=%s total_questions=%s unanswered=%s",
                rfp_id,
                len(questions),
                len(to_answer),
            )

            new_answers, new_answers_by_q = [], {}
            if to_answer:
                try:
                    new_answers, new_answers_by_q = await self._generate_new_answers(store, to_answer)
                except Exception:
                    logger.exception(
                        "Bulk answer generation failed rfp_id=%s unanswered=%s model=%s",
                        rfp_id,
                        len(to_answer),
                        self._config.answer_model,
                    )
                    raise

            if new_answers:
                store.bulk_insert_answers(new_answers)
                store.commit()
                logger.info("Inserted bulk answers rfp_id=%s inserted=%s", rfp_id, len(new_answers))

            result_questions = already_answered + to_answer
            return {
                "rfp_id": rfp_id,
                "questions": [
                    {
                        "id": q.id,
                        "content": q.content,
                        "answers": [a.to_dict() for a in q.answers] if q.answers else [a.to_dict() for a in new_answers_by_q.get(q.id, [])],
                    }
                    for q in result_questions
                ],
            }

    async def _generate_new_answers(self, store : Persistence, questions : list) -> tuple:
            """Generate and map new answers for unanswered questions in one bulk LLM call."""
            new_answers: List[Answer] = []
            new_answers_by_q: dict[int, List[Answer]] = {}

            # Embed unanswered questions for vector retrieval.
            embeddings = self._embedder([q.content for q in questions])

            prompt_questions = self._build_prompt(store, questions, embeddings)
            # Send one bulk prompt to the LLM.

            try:
                responses = await generate_answers(
                    self._generative_client,
                    self._config.answer_prompt_path,
                    self._config.answer_model,
                    question_text=json.dumps(prompt_questions),
                )
            except Exception:
                logger.exception(
                    "LLM bulk call failed question_count=%s model=%s",
                    len(questions),
                    self._config.answer_model,
                )
                raise

            # Map generated responses back to question IDs.
            mapped_all = map_answers(
                responses,
                [q.id for q in questions],
                answer_version_id= self._get_version_id(store, self._config.answer_version_name) if self._answer_version_id is None else self._answer_version_id,
            )

            new_answers.extend(mapped_all)
            new_answers_by_q = {
                q.id: mapped_all[i : i + 1] for i, q in enumerate(questions)
            }

            return new_answers, new_answers_by_q

    def _build_prompt(self, store : Persistence, questions, embeddings) -> list:
        """Build per-question prompt payloads with retrieval context from similar chunks."""
        prompt_questions = []

        for question, q_emb in zip(questions, embeddings):
            chunks = list(
                store.get_most_similar_chunks(
                    q_emb,
                    self._config.min_similarity,
                    self._config.top_k,
                    chunk_version_name=self._config.chunk_version_name,
                )
            )
            context = " | ".join([c.content for c in chunks]) if chunks else ""
            prompt_questions.append({"question" : question.content, "context" : context})

        return prompt_questions


    def _get_version_id(self, store : Persistence, version_name : str):
        """Resolve and cache the configured answer version id for bulk inserts."""
        version = store.get_answer_version_by_name(version_name)

        if version is None:
            err_msg = f'No answer version with name {version_name}'
            logger.warning(err_msg)
            raise DatabaseQueryError(err_msg)

        self._answer_version_id = version.id
        return self._answer_version_id
