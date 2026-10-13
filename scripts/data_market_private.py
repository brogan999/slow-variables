"""Build the owner's private page for the data market (plan Part 57h). Local only; never deployed.

    uv run python scripts/data_market_private.py <private folder> <output.html>

The private folder is outside the repository and holds the playbook (playbook-private.md), a private note for each
dossier (dossiers/D<number>.md) and vendor (vendors/<id>*.md), and, optionally, questions.json: the state of each
question only a buyer can answer ([{"n": 1, "status": "asked", "asked_on": "...", "answer": "..."}]). This joins them
to the site's own export and writes one self-contained HTML file. It refuses to write inside the repository.

The page opens on the revenue streams, then the buyer questions with where each stands, then the rest of the playbook,
then the public market view with the private note beside every record that has one.
"""

from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "web" / "data"

CSS = """
:root{--bg:#f2f0ec;--surface:#fff;--ink:#161d22;--ink2:#465058;--muted:#7b858c;--grid:#dcd8d0;--slow:#00897b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,"Helvetica Neue",Arial,sans-serif}
.bar{background:#000;color:#fff;font-size:12px;letter-spacing:.14em;text-transform:uppercase;padding:8px 20px;position:sticky;top:0;z-index:2}
.bar a{color:#fff;margin-left:18px;text-decoration:none;opacity:.8}
main{max-width:70rem;margin:0 auto;padding:28px 20px 80px}h1{font-size:2.4rem;line-height:1.05;margin:.2em 0 .4em;letter-spacing:-.02em}
h2{font-size:1.5rem;margin:2.2em 0 .5em;border-top:1px solid var(--grid);padding-top:1em}h3{font-size:1.1rem;margin:1.4em 0 .3em}h4{margin:1.2em 0 .2em}
p,li{max-width:74ch}a{color:inherit;text-decoration-color:var(--grid);text-underline-offset:3px}
.panel{background:var(--surface);box-shadow:0 0 0 1px var(--grid);border-radius:4px;padding:14px 18px;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:.6em 0;display:block;overflow-x:auto}th,td{text-align:left;vertical-align:top;padding:6px 10px;border-bottom:1px solid var(--grid)}
th{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}code{font:12.5px ui-monospace,Menlo,monospace;background:#eceae5;padding:1px 4px;border-radius:2px}
details{margin:6px 0}summary{cursor:pointer;font-weight:600}summary .n{font-weight:400;color:var(--muted);font-variant-numeric:tabular-nums;margin-right:.5em}
.chip{display:inline-block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;border:1px dashed var(--muted);color:var(--muted);padding:1px 6px;border-radius:2px}
.chip.done{border:1px solid var(--slow);color:var(--slow)}.note{border-left:3px solid #000;padding-left:14px;margin:10px 0}.pub{color:var(--ink2)}.muted{color:var(--muted);font-size:12.5px}
"""


def inline(text: str) -> str:
    t = escape(text)  # quotes too: an address is written into an attribute
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\w)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', t)
    return re.sub(r'(?<!["=>])(https?://[^\s<)]+)', r'<a href="\1">\1</a>', t)


def markdown(text: str, shift: int = 0) -> str:
    """Enough markdown for the private notes: headings, paragraphs, lists, tables, quotes, rules and inline marks."""
    out, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif m := re.match(r"(#{1,5}) (.*)", line):
            level = min(6, len(m.group(1)) + shift)
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
        elif line.strip() in ("---", "***"):
            out.append("<hr>")
            i += 1
        elif (
            line.lstrip().startswith("|")
            and i + 1 < len(lines)
            and re.match(r"\s*\|[\s:|-]+\|\s*$", lines[i + 1])
        ):
            cells = lambda row: [c.strip() for c in row.strip().strip("|").split("|")]  # noqa: E731
            head, rows, i = cells(line), [], i + 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(
                "<table><thead><tr>"
                + "".join(f"<th>{inline(c)}</th>" for c in head)
                + f"</tr></thead><tbody>{body}</tbody></table>"
            )
        elif re.match(r"\s*([-*]|\d+\.) ", line):
            tag = "ol" if re.match(r"\s*\d+\. ", line) else "ul"
            items = []
            while i < len(lines) and (
                re.match(r"\s*([-*]|\d+\.) ", lines[i]) or (lines[i].startswith("  ") and lines[i].strip())
            ):
                if re.match(r"\s*([-*]|\d+\.) ", lines[i]):
                    items.append(re.sub(r"^\s*([-*]|\d+\.) ", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
        elif line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip("> "))
                i += 1
            out.append(f"<blockquote>{inline(' '.join(quote))}</blockquote>")
        else:
            para = [line.strip()]  # this line is taken whatever it opens with, so the loop always moves on
            i += 1
            while (
                i < len(lines)
                and lines[i].strip()
                and not re.match(r"(#{1,5} |\s*([-*]|\d+\.) |>|\s*\|)", lines[i])
            ):
                para.append(lines[i].strip())
                i += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


def sections(text: str) -> list[tuple[str, str]]:
    """The playbook's second-level sections, as (title, body)."""
    parts = re.split(r"^## (.+)$", text, flags=re.M)
    return [(parts[k].strip(), parts[k + 1]) for k in range(1, len(parts) - 1, 2)]


def read(p: Path) -> str:
    return p.read_text() if p.exists() else ""


def main(args: list[str]) -> None:
    private, out = Path(args[0]).resolve(), Path(args[1]).resolve()
    if out.is_relative_to(ROOT):
        sys.exit("refused: the private page must be written outside the repository")
    market = json.loads((DATA / "data_market.json").read_text())
    dossiers = json.loads((DATA / "data_market_dossiers.json").read_text())
    secs = sections(read(private / "playbook-private.md"))
    is_stream = lambda t: bool(re.search(r"\bStream\b|five openings", t))  # noqa: E731
    is_questions = lambda t: "Questions only a buyer" in t  # noqa: E731
    state = {q["n"]: q for q in json.loads(read(private / "questions.json") or "[]")}

    html = [
        f'<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content=\'width=device-width,initial-scale=1\'><meta name="robots" content="noindex,nofollow"><title>Data market playbook (private)</title><style>{CSS}</style>'
    ]
    html.append(
        '<div class=bar>Private · local file · never deployed<a href="#streams">Streams</a><a href="#questions">Questions</a><a href="#rest">Playbook</a><a href="#signals">Signals</a><a href="#vendors">Vendors</a><a href="#dossiers">Dossiers</a></div><main>'
    )
    html.append(
        "<h1>The data market: how I would build it</h1><p class=muted>Built from the private folder and the site's own export. The public site shows the market; this page adds the routes, the terms, the people to ask and the legal lines.</p>"
    )

    html.append('<h2 id="streams">The streams</h2>')
    for title, body in secs:
        if is_stream(title):
            html.append(
                f"<div class=panel><h3>{inline(re.sub(r'^\d+\.\s*', '', title))}</h3>{markdown(body, shift=2)}</div>"
            )

    html.append('<h2 id="questions">Questions only a buyer can answer</h2>')
    for title, body in secs:
        if is_questions(title):
            asked = re.findall(r"^\s*(\d+)\.\s+(.*)$", body, flags=re.M)
            rows = []
            for n, q in asked:
                s = state.get(int(n), {})
                chip = (
                    f"<span class='chip done'>{escape(s['status'])}</span>"
                    if s.get("status")
                    else "<span class=chip>not asked yet</span>"
                )
                rows.append(
                    f"<tr><td>{n}</td><td>{inline(q)}</td><td>{chip}<br><span class=muted>{escape(str(s.get('asked_on') or ''))}</span></td><td>{inline(str(s.get('answer') or ''))}</td></tr>"
                )
            html.append(
                "<table><thead><tr><th>#</th><th>Question</th><th>Where it stands</th><th>Answer</th></tr></thead><tbody>"
                + "".join(rows)
                + "</tbody></table>"
            )
            html.append(
                "<p class=muted>Edit questions.json in the private folder to record an answer, then rebuild.</p>"
            )

    html.append('<h2 id="rest">The rest of the playbook</h2>')
    for title, body in secs:
        if not is_stream(title) and not is_questions(title):
            html.append(f"<details><summary>{inline(title)}</summary>{markdown(body, shift=2)}</details>")

    html.append(
        f'<h2 id="signals">What the vendors\' pages show <span class=muted>{market["counts"]["signals"]} signals, most-shown first</span></h2><table><thead><tr><th>Vendors</th><th>Signal</th><th>What it implies buyers want</th></tr></thead><tbody>'
    )
    for s in market["signals"][:60]:
        html.append(
            f"<tr><td>{s['evidenced']}{' +' + str(s['weak']) if s['weak'] else ''}</td><td>{escape(s['headline'])}</td><td class=pub>{escape(s['implies'])}</td></tr>"
        )
    html.append("</tbody></table>")

    html.append('<h2 id="vendors">Vendors, with the private note on each</h2>')
    for v in sorted(market["vendors"], key=lambda v: (-len(v["signals"]), v["name"].lower())):
        note = "\n\n".join(read(p) for p in sorted((private / "vendors").glob(f"{v['id']}*.md")))
        body = f"<p class=pub>{escape(v['sells'])}</p>" + (
            f"<div class=note>{markdown(note, shift=3)}</div>"
            if note
            else "<p class=muted>No private note.</p>"
        )
        html.append(
            f"<details><summary><span class=n>{len(v['signals'])}</span>{escape(v['name'])}{' <span class=chip>weak evidence</span>' if v['evidence'] == 'weak' else ''}</summary>{body}</details>"
        )

    html.append('<h2 id="dossiers">Dossiers, with the private half of each</h2>')
    for d in dossiers:
        note = read(private / "dossiers" / f"D{d['n']:02d}.md")
        body = (
            f"<div class=note>{markdown(note, shift=3)}</div>"
            if note
            else "<p class=muted>No private dossier.</p>"
        )
        html.append(
            f"<details><summary><span class=n>{d['n']}</span>{escape(d['title'])}</summary>{body}</details>"
        )

    html.append("</main></html>")
    out.write_text("\n".join(html))
    print(
        f"wrote {out.name}: {sum(is_stream(t) for t, _ in secs)} streams, {len(market['vendors'])} vendors, {len(dossiers)} dossiers"
    )


if __name__ == "__main__":
    main(sys.argv[1:])
