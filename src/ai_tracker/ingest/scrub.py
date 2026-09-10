"""Prompt-injection hygiene: HTML -> text with hidden nodes dropped; agent-directed sentences removed and returned."""

from __future__ import annotations

import re
from html.parser import HTMLParser

AGENT_RE = re.compile(
    r"(?i)(ignore (all |any |the )?(previous|prior|above) instructions"
    r"|you are an? (ai|llm|language model|assistant)\b"
    r"|(to|for|attention|note to) (any |all )?(ai|llm) (agents?|assistants?|crawlers?|models?)"
    r"|\bas an ai\b|system prompt|<\|im_start\|>|\[INST\]|^\s*(assistant|system):)"
)
SKIP_TAGS = {"script", "style", "noscript", "template"}
BLOCK = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "td", "th", "section", "article", "br", "pre"}
VOID = {"br", "img", "input", "hr", "meta", "link", "area", "base", "col", "embed", "source", "track", "wbr"}
HIDDEN = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden")


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        hidden = (
            tag in SKIP_TAGS
            or "hidden" in a
            or a.get("aria-hidden") == "true"
            or bool(HIDDEN.search(a.get("style") or ""))
        )
        if hidden and tag not in VOID:
            self.stack.append(tag)
        elif not self.stack and tag in BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif not self.stack and tag in BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.stack:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    p = _Text()
    p.feed(html)
    return re.sub(r"[ \t]+", " ", "".join(p.parts))


def scrub(text: str) -> tuple[str, list[str]]:
    keep: list[str] = []
    flagged: list[str] = []
    for seg in re.split(r"(?<=[.!?\n])\s+", text):
        (flagged if AGENT_RE.search(seg) else keep).append(seg)
    return " ".join(s.strip() for s in keep if s.strip()), [f.strip()[:200] for f in flagged]


def normalise(text: str) -> str:
    """Whitespace-insensitive form used for snippet-in-page assertions."""
    return re.sub(r"\s+", " ", text).strip()
