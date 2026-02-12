import logging

from answer_gen.storage.db import build_connection
from answer_gen.storage import Question, Answer
from answer_gen.storage.persistence import Persistence
from answer_gen.utils.generative import generate_single_answer
from answer_gen.utils.generative.mappers import map_answers

from answer_gen.utils.embedder import Embedder
from answer_gen.exceptions import InvalidResourceIdentifier
import answer_gen.exceptions as exceptions

from answer_gen.utils.config.answer_worker_config import AnswerWorkerConfig

logger = logging.getLogger(__name__)

class AnswerWorker:
    def __init__(
        self,
        db_url: str,
        generative_client,
        config : AnswerWorkerConfig
    ):
        """Initialize answer generation dependencies and runtime configuration."""
        self._db_url = db_url
        self._generative_client = generative_client
        self._embedder = Embedder(config.embedding_model, batch_size = config.embedding_batch_size)
        self._config = config

    async def __call__(self, question_id: int):
        """Generate and persist answers for a question, or return cached answers."""
        with build_connection(self._db_url) as session:
            # Persistence facade wraps all DB access for this unit of work.
            store = Persistence(session)

            question: Question = store.get_question_by_id(question_id)
            if question is None:
                logger.warning("Question not found question_id=%s", question_id)
                raise InvalidResourceIdentifier(f"Question with id {question_id} does not exist in the database.")

            # If answers already exist, return them
            if question.answers:
                logger.info("Returning cached answers question_id=%s count=%s", question.id, len(question.answers))
                return {"question": question.id, "answers": [a.to_dict() for a in question.answers]}

            # Retrieve best matching chunk by vector similarity
            question_embedding = self._embedder([question.content])[0]
            chunks = list(store.get_most_similar_chunks(
                question_embedding,
               self._config.min_similarity,
                self._config.top_k,
                chunk_version_name=self._config.chunk_version_name,
            ))
            if not chunks:
                logger.info("No similar chunks found question_id=%s", question.id)
                return {"question": question.id, "answers": []}

            # TODO: deal with prompt sizing
            context = " | ".join([c.content for c in chunks])

            try:
                answer_response = await generate_single_answer(
                    self._generative_client,
                    self._config.answer_prompt_path,
                    self._config.answer_model,
                    question_text=question.content,
                    context=context,
                )
            except Exception:
                logger.exception(
                    "Failed to generate answer question_id=%s model=%s chunk_count=%s",
                    question.id,
                    self._config.answer_model,
                    len(chunks),
                )
                raise

            if answer_response is None:
                logger.exception(
                    "No answer returned from generator question_id=%s model=%s",
                    question_id,
                    self._config.answer_model,
                )
                raise exceptions.GenerativeOutputError(f'Failed to generate an answer for {question_id}')

            # Convert LLM output into ORM Answer rows.
            answers = map_answers(
                [answer_response],
                question_ids=[question.id],
                answer_version_id=self._get_answer_version_id(store) if self._config.answer_version_name is not None else None,
            )

            # Persist newly generated answers for future cache hits.
            store.bulk_insert_answers(answers)
            store.commit()
            logger.info("Generated answers question_id=%s count=%s", question.id, len(answers))

            return {"question": question.id, "answers": [a.to_dict() for a in answers]}

    def _get_answer_version_id(self, store : Persistence) -> int:
        """Resolve and cache the configured answer version id."""
        answer_version = store.get_answer_version_by_name(self._config.answer_version_name)

        if answer_version is None:
            logger.warning(f'No answer version with name: {self._config.answer_version_name}')
            raise exceptions.DatabaseQueryError(f'Could not find answer version with name {self._config.answer_version_name}')

        self._answer_version = answer_version.id
        return self._answer_version

    def fetch_answer(self, answer_id) -> dict:
        """Fetch one answer by id and return it as an API-friendly payload."""
        with build_connection(self._db_url) as session:
            store = Persistence(session)
            answer : Answer = store.get_answer_by_id(answer_id)

            if answer is None:
                logger.warning(f'No answer with ID {answer_id}.')
                raise exceptions.InvalidResourceIdentifier(f'Could not find an answer with the given identifier.')

        return {"answer" : answer.to_dict()}
