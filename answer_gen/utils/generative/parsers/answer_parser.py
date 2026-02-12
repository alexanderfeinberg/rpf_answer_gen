import json
from answer_gen.utils.utils import extract_json
from answer_gen.exceptions import InvalidGenerativeResponseStructure
from pydantic import BaseModel, ValidationError

class GenerativeAnswerResponse(BaseModel):
    """Structured representation of one answer item returned by the LLM."""

    answer : str
    confidence : str | None
    sources : list[int] | int | str
    coverage : str | None
    notes : str | None

    @classmethod
    def from_dict(cls, data : dict):
        """Build a typed response object from an answer dictionary payload."""
        return GenerativeAnswerResponse(
            answer = data.get("answer", None),
            confidence = data.get("confidence", None),
            sources = data.get("sources_used", []),
            coverage = data.get("coverage", None),
            notes = data.get("notes", None)
        )

def parse_answer_json(text: str) -> list[GenerativeAnswerResponse]:
    """Parse LLM output into a list of GenerativeAnswerResponse."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = json.loads(extract_json(text))

    if isinstance(payload, dict) and "answers" in payload:
        answers = payload["answers"]
    else:
        answers = payload

    out: list[str] = []
    if isinstance(answers, list):
        for item in answers:
            if isinstance(item, str):
                raise InvalidGenerativeResponseStructure('Answers must a list of dictionaries. Got list of strings.')
            elif isinstance(item, dict):
                try:
                    response = GenerativeAnswerResponse.from_dict(item)
                except ValidationError as e:
                    err_msg = e.errors()[0]['type']
                    raise InvalidGenerativeResponseStructure('Failed to validate structure of answer: ' + str(err_msg))

                out.append(response)

    return out
