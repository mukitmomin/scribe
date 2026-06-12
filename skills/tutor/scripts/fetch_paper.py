#!/usr/bin/env python3
"""Fetch an arXiv paper as plain text.

Without --section: print a numbered section list + abstract (~1k tokens).
With --section N: print that section's text (~4k token hard cap).
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from _state import ensure_state

USER_AGENT = "scribe/2.0 (+https://github.com/mukitmomin/scribe)"
TIMEOUT = 25
# ~4 chars per token rule of thumb.
SECTION_CHAR_CAP = 16_000
LIST_CHAR_CAP = 4_000

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}

HEADING_TAGS = {"h1", "h2", "h3"}
BLOCK_TAGS = {
    "p", "li", "br", "tr", "div", "section", "article", "header", "footer",
    "blockquote", "pre", "figure", "figcaption", "table", "thead", "tbody",
}
SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside", "noscript", "svg"}


class _Extract(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self._heading: list[str] | None = None
        # List of (level, title, body_text).
        self.sections: list[tuple[int, str, list[str]]] = []
        self._current_body: list[str] = []

    def handle_starttag(self, tag: str, attrs):  # noqa: ANN001
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag in HEADING_TAGS:
            # Flush any heading-in-progress just in case.
            self._heading = []
            self._heading_level = int(tag[1])
            return
        if tag in BLOCK_TAGS:
            self._current_body.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if tag in HEADING_TAGS and self._heading is not None:
            title = re.sub(r"\s+", " ", "".join(self._heading)).strip()
            self.sections.append((self._heading_level, title, []))
            self._current_body = self.sections[-1][2]
            self._heading = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._heading is not None:
            self._heading.append(data)
            return
        self._current_body.append(data)


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _flatten(parts: list[str]) -> str:
    text = "".join(parts)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_html(aid: str) -> tuple[str, str] | None:
    """Try arxiv.org/html then ar5iv. Returns (html_bytes_as_text, source_url) or None."""
    for url in (f"https://arxiv.org/html/{aid}", f"https://ar5iv.labs.arxiv.org/html/{aid}"):
        try:
            data = _get(url).decode("utf-8", errors="replace")
            if data and "<html" in data.lower():
                return data, url
        except Exception as e:  # noqa: BLE001
            print(f"scribe: {url} failed: {e}", file=sys.stderr)
    return None


def fetch_abstract(aid: str) -> tuple[str, str]:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": aid})
    data = _get(url)
    root = ET.fromstring(data)
    entry = root.find("a:entry", ATOM_NS)
    if entry is None:
        return aid, ""
    title = (entry.findtext("a:title", default="", namespaces=ATOM_NS) or "").strip()
    abstract = (entry.findtext("a:summary", default="", namespaces=ATOM_NS) or "").strip()
    title = re.sub(r"\s+", " ", title)
    abstract = re.sub(r"\s+", " ", abstract)
    return title, abstract


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--id", required=True, help="arXiv id, e.g. 1706.03762")
    p.add_argument("--section", type=int, default=None, help="section index (1-based)")
    args = p.parse_args()

    ensure_state()

    aid = args.id.strip()
    if "v" in aid:
        head, _, tail = aid.partition("v")
        if tail.isdigit():
            aid = head

    got = fetch_html(aid)
    if got is None:
        title, abstract = fetch_abstract(aid)
        print(f"# {title or aid}")
        print()
        print("[full text unavailable — showing abstract only]")
        print()
        print(abstract)
        return 0

    raw_html, source = got
    parser = _Extract()
    try:
        parser.feed(raw_html)
    except Exception as e:  # noqa: BLE001
        print(f"scribe: html parse failed: {e}", file=sys.stderr)

    sections = parser.sections
    # Build top-level sections by treating any heading as a break.
    # Filter empty.
    cleaned: list[tuple[str, str]] = []
    for _level, title, body in sections:
        text = _flatten(body)
        if not title:
            continue
        cleaned.append((title, text))

    title, abstract = fetch_abstract(aid)

    if args.section is None:
        print(f"# {title or aid}")
        print(f"source: {source}")
        print()
        print("## Abstract")
        print()
        print(abstract or "(unavailable)")
        print()
        print("## Sections")
        if not cleaned:
            print("(no sections parsed)")
            return 0
        out_lines: list[str] = []
        for i, (sec_title, _body) in enumerate(cleaned, start=1):
            out_lines.append(f"{i}. {sec_title}")
        listing = "\n".join(out_lines)
        if len(listing) > LIST_CHAR_CAP:
            listing = listing[:LIST_CHAR_CAP].rstrip() + "\n…(truncated)"
        print(listing)
        return 0

    idx = args.section - 1
    if idx < 0 or idx >= len(cleaned):
        print(f"scribe: section {args.section} out of range (1..{len(cleaned)})", file=sys.stderr)
        return 2
    sec_title, body = cleaned[idx]
    print(f"# {sec_title}")
    print()
    if len(body) > SECTION_CHAR_CAP:
        body = body[:SECTION_CHAR_CAP].rstrip() + "\n…(truncated)"
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
