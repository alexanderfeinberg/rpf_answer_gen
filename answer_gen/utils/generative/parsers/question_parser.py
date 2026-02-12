import json
from answer_gen.utils.utils import extract_json

def parse_questions_json(text: str) -> list[str]:
    """Parse LLM output into a list of question strings."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = json.loads(extract_json(text))

    if isinstance(payload, dict) and "questions" in payload:
        questions = payload["questions"]
    else:
        questions = payload

    out: list[str] = []
    if isinstance(questions, list):
        for item in questions:
            if isinstance(item, str):
                out.append(item.strip())
            elif isinstance(item, dict) and "text" in item:
                out.append(str(item["text"]).strip())

    return [q for q in out if q]
