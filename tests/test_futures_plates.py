"""An idea's illustration is shown at the size it was made: the generated set is one 720-pixel file each."""

from pathlib import Path

PARTS = (Path(__file__).resolve().parents[1] / "web" / "src" / "components" / "FuturesParts.tsx").read_text()


def test_an_ideas_plate_is_not_shown_at_half_its_size():
    card = PARTS.split("export function IdeaCard")[1].split("export function")[0]
    assert "max-w-[720px]" in card and "max-w-[360px]" not in card
    assert "720px" in card.split("sizes=")[1].split('"')[1], (
        "the browser is told the size it will be drawn at"
    )
