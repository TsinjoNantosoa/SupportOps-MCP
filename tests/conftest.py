from __future__ import annotations

from pathlib import Path

import pytest

from supportops.config import project_root
from supportops.services.ticket_service import TicketService
from supportops.storage.seed import initialize_database


@pytest.fixture
def db(tmp_path: Path):
    return initialize_database(tmp_path / "supportops.db", reset=True)


@pytest.fixture
def tickets(db):
    return TicketService(db)


@pytest.fixture
def knowledge_dir() -> Path:
    return project_root() / "knowledge"
