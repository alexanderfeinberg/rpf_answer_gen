from __future__ import annotations

from dataclasses import dataclass

from answer_gen.utils.config.config_utils import read_config, get_config_str


@dataclass(frozen=True, slots=True)
class QuestionWorkerConfig:
    """Typed configuration container for `QuestionWorker` settings."""

    prompt_path: str
    model: str

    @classmethod
    def from_config(cls, config_path: str = "config/global.ini") -> "QuestionWorkerConfig":
        """Build question worker config values from the configured INI file."""
        read_config(config_path)
        prompt = get_config_str("question_parsing", "parsing_prompt_path", "")
        model = get_config_str("question_parsing", "model", "gpt-4o-mini")
        return cls(prompt_path=prompt, model=model)
