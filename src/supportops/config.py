from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    root: Path
    db_path: Path
    knowledge_dir: Path
    session_id: str
    user_id: str
    model: str

    @classmethod
    def load(cls) -> Settings:
        load_dotenv()
        root = project_root()
        raw_db = Path(os.getenv("SUPPORTOPS_DB_PATH", ".supportops/supportops.db"))
        db_path = raw_db if raw_db.is_absolute() else root / raw_db
        return cls(
            root=root,
            db_path=db_path,
            knowledge_dir=root / "knowledge",
            session_id=os.getenv("SUPPORTOPS_SESSION_ID", "local-demo"),
            user_id=os.getenv("SUPPORTOPS_USER", "local-operator"),
            model=os.getenv("OPENAI_MODEL", "gpt-6-astra"),
        )
