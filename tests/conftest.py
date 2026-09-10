import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ai_tracker.ingest.base import RawItem

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def raw():
    def make(name: str, url: str = "https://example.test/x") -> RawItem:
        body = (FIX / name).read_bytes()
        return RawItem(
            url, body, 200, datetime(2026, 9, 10, tzinfo=timezone.utc), hashlib.sha256(body).hexdigest(), None
        )

    return make
