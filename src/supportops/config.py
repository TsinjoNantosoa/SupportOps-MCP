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
    model: str | None
    ticketing_host: str
    ticketing_port: int
    knowledge_host: str
    knowledge_port: int
    mcp_transport: str
    mcp_bearer_token: str | None
    allowed_hosts: tuple[str, ...]
    allowed_origins: tuple[str, ...]
    max_request_body_size: int
    approval_host: str
    approval_port: int
    approval_api_token: str | None
    remote_approval_enabled: bool
    authorized_approvers: tuple[str, ...]
    approval_allowed_hosts: tuple[str, ...]

    @classmethod
    def load(cls) -> Settings:
        load_dotenv()
        root = project_root()
        raw_db = Path(os.getenv("SUPPORTOPS_DB_PATH", ".supportops/supportops.db"))
        db_path = raw_db if raw_db.is_absolute() else root / raw_db
        raw_knowledge = Path(os.getenv("SUPPORTOPS_KNOWLEDGE_DIR", "knowledge"))
        knowledge_dir = raw_knowledge if raw_knowledge.is_absolute() else root / raw_knowledge
        ticketing_host = os.getenv("SUPPORTOPS_TICKETING_HOST", "127.0.0.1")
        ticketing_port = int(os.getenv("SUPPORTOPS_TICKETING_PORT", "8001"))
        knowledge_host = os.getenv("SUPPORTOPS_KNOWLEDGE_HOST", "127.0.0.1")
        knowledge_port = int(os.getenv("SUPPORTOPS_KNOWLEDGE_PORT", "8002"))
        default_hosts = (
            f"localhost:{ticketing_port}",
            f"127.0.0.1:{ticketing_port}",
            f"localhost:{knowledge_port}",
            f"127.0.0.1:{knowledge_port}",
        )
        allowed_hosts = _csv_env("SUPPORTOPS_ALLOWED_HOSTS", default_hosts)
        allowed_origins = _csv_env(
            "SUPPORTOPS_ALLOWED_ORIGINS",
            ("http://localhost:5678", "http://127.0.0.1:5678"),
        )
        model = os.getenv("OPENAI_MODEL", "").strip() or None
        token = os.getenv("SUPPORTOPS_MCP_BEARER_TOKEN", "").strip() or None
        return cls(
            root=root,
            db_path=db_path,
            knowledge_dir=knowledge_dir,
            session_id=os.getenv("SUPPORTOPS_SESSION_ID", "local-demo"),
            user_id=os.getenv("SUPPORTOPS_USER", "local-operator"),
            model=model,
            ticketing_host=ticketing_host,
            ticketing_port=ticketing_port,
            knowledge_host=knowledge_host,
            knowledge_port=knowledge_port,
            mcp_transport=os.getenv("SUPPORTOPS_MCP_TRANSPORT", "stdio").lower(),
            mcp_bearer_token=token,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
            max_request_body_size=int(os.getenv("SUPPORTOPS_MAX_REQUEST_BODY_SIZE", "1048576")),
            approval_host=os.getenv("SUPPORTOPS_APPROVAL_HOST", "127.0.0.1"),
            approval_port=int(os.getenv("SUPPORTOPS_APPROVAL_PORT", "8010")),
            approval_api_token=(os.getenv("SUPPORTOPS_APPROVAL_API_TOKEN", "").strip() or None),
            remote_approval_enabled=_bool_env("SUPPORTOPS_REMOTE_APPROVAL_ENABLED", False),
            authorized_approvers=_csv_env("SUPPORTOPS_AUTHORIZED_APPROVERS", ()),
            approval_allowed_hosts=_csv_env(
                "SUPPORTOPS_APPROVAL_ALLOWED_HOSTS", ("localhost", "127.0.0.1")
            ),
        )


def _csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if raw is None:
        return default
    return tuple(value.strip() for value in raw.split(",") if value.strip())


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
