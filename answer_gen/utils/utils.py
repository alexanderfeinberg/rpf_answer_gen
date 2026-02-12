import json

def extract_json(text: str) -> str:
    """Best-effort JSON object/array extraction from a noisy LLM response."""
    start = min([i for i in [text.find("{"), text.find("[")] if i != -1], default=-1)
    if start == -1:
        raise json.JSONDecodeError("No JSON found", text, 0)

    # Greedy scan for matching closing bracket.
    open_char = text[start]
    close_char = "}" if open_char == "{" else "]"
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    raise json.JSONDecodeError("Unterminated JSON", text, start)
