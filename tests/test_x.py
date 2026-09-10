import json
from datetime import date, datetime, timezone
from pathlib import Path

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.x import XDrop, XList


def item(body: bytes, url: str = "https://publish.x.com/oembed?url=x") -> RawItem:
    return RawItem(url, body, 200, datetime(2026, 9, 10, tzinfo=timezone.utc), "h" * 64)


def test_drop_extracts_handle_text_and_date_from_oembed():
    body = Path("tests/fixtures/x_oembed_jack.json").read_bytes()
    rows = XDrop.extract(XDrop.__new__(XDrop), [item(body)])
    assert len(rows) == 1
    r = rows[0]
    assert r.series_key == "watch.x.jack.pt" and r.value_text == "just setting up my twttr"
    assert r.as_of_date == date(2006, 3, 21) and int(r.tier) == 7 and r.url == "https://x.com/jack/status/20"


def test_list_extracts_from_api_json_and_keeps_external_links():
    body = json.dumps(
        {
            "data": [
                {
                    "id": "1",
                    "author_id": "u1",
                    "created_at": "2026-09-09T12:00:00.000Z",
                    "text": "New paper out https://t.co/abc",
                    "entities": {"urls": [{"expanded_url": "https://arxiv.org/abs/2609.00001"}]},
                }
            ],
            "includes": {"users": [{"id": "u1", "username": "METR_Evals"}]},
        }
    ).encode()
    c = XList.__new__(XList)
    rows = XList.extract(c, [item(body, "https://api.x.com/2/lists/1/tweets")])
    assert (
        rows[0].series_key == "watch.x.metr_evals.pt"
        and "links: https://arxiv.org/abs/2609.00001" in rows[0].value_text
    )
    assert rows[0].url == "https://x.com/METR_Evals/status/1"
