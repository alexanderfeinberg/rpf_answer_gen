from __future__ import annotations

from typing import Iterable, List, Sequence

from answer_gen.storage import Answer, Question
from answer_gen.storage.factories import answer_factory, question_factory
from answer_gen.utils.generative.parsers.answer_parser import GenerativeAnswerResponse


def map_answers(
    responses: Sequence[GenerativeAnswerResponse],
    question_ids: int | Sequence[int],
    answer_version_id: int | None = None,
) -> List[Answer]:
    """Convert parsed LLM answers into Answer ORM instances.

    - If ``question_ids`` is a single int, all responses map to that question.
    - If it's a sequence, it must align 1:1 with responses.
    """

    if isinstance(question_ids, int):
        ids = [question_ids] * len(responses)
    else:
        if len(question_ids) != len(responses):
            raise ValueError("question_ids length must match responses length")
        ids = list(question_ids)

    return [
        answer_factory(
            content=resp.answer,
            question_id=qid,
            answer_version_id=answer_version_id,
        )
        for qid, resp in zip(ids, responses)
    ]


def map_questions(questions: Iterable[str], rfp_id: int) -> List[Question]:
    """Convert parsed question strings into Question ORM instances."""
    normalized = [q.strip() for q in questions if q and q.strip()]
    return [question_factory(content=q, rfp_id=rfp_id) for q in normalized]
