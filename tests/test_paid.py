from datetime import date

from ai_tracker.ingest.connectors.paid import PAID


def test_paid_stubs_refuse_clearly(monkeypatch):
    monkeypatch.delenv("PAID_SOURCES", raising=False)
    for cls in PAID:
        rows, log = cls().run(date(2026, 9, 11))
        assert rows == [] and not log.ok and "PAID_SOURCES=true" in (log.error or "") and cls.optional
