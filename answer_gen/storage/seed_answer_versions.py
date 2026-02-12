from __future__ import annotations

import sys

from sqlalchemy import select

from answer_gen.storage import AnswerVersion
from answer_gen.storage.db import build_bulk_connection
from answer_gen.utils.config.config_utils import read_config, get_config_str
import os

from dotenv import load_dotenv


def _load_answer_version_name(config_path: str) -> str:
    config = read_config(config_path)
    # Prefer an explicit answer_version if/when you add it.
    if config.has_option("answers", "answer_version"):
        return get_config_str("answers", "answer_version", "v1")

    # Fallback to embedding_version until answer-specific versioning is defined.
    return get_config_str("embedding", "embedding_version", "v1")


def seed_answer_versions(db_url: str, config_path: str) -> str:
    """Ensure the configured answer version exists in answer_versions."""
    version_name = _load_answer_version_name(config_path)

    with build_bulk_connection(db_url) as session:
        existing = session.execute(
            select(AnswerVersion).where(AnswerVersion.version_name == version_name)
        ).scalar_one_or_none()

        if existing is not None:
            print(f"AnswerVersion already exists: {version_name} (id={existing.id})")
            return version_name

        session.add(AnswerVersion(version_name=version_name))
        session.commit()
        print(f"Inserted AnswerVersion: {version_name}")
        return version_name


def main(argv: list[str]) -> int:
    load_dotenv()

    if len(argv) < 2:
        print("Usage: python -m answer_gen.storage.seed_answer_versions <config_path> <db_url> ")
        return 2

    config_path = argv[1] if len(argv) >= 2 else "config/global.ini"

    db_url = argv[2] if len(argv) >= 3 else os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError('No database URL provided.')

    seed_answer_versions(db_url, config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
