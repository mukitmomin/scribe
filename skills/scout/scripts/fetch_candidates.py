#!/usr/bin/env python3
"""Fetch candidate arXiv papers across arXiv, HN, and HuggingFace.

Stdout: JSONL, one paper per line. Network failures on individual sources
warn to stderr and continue.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from _state import ensure_state, scribe_home


ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")
ATOM_NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
USER_AGENT = "scribe/2.0 (+https://github.com/mukitmomin/scribe)"
TIMEOUT = 20


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _norm_id(raw: str) -> str | None:
    m = ARXIV_ID_RE.search(raw)
    return m.group(1) if m else None


def _truncate(text: str, n: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def fetch_arxiv(query: str, since: datetime) -> list[dict]:
    params = {
        "search_query": f"all:{query}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": "50",
    }
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    data = _get(url)
    root = ET.fromstring(data)
    out: list[dict] = []
    for entry in root.findall("a:entry", ATOM_NS):
        id_url = (entry.findtext("a:id", default="", namespaces=ATOM_NS) or "").strip()
        aid = _norm_id(id_url)
        if not aid:
            continue
        published = (entry.findtext("a:published", default="", namespaces=ATOM_NS) or "").strip()
        try:
            pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            continue
        if pub_dt < since:
            continue
        title = _truncate(entry.findtext("a:title", default="", namespaces=ATOM_NS) or "", 300)
        abstract = _truncate(entry.findtext("a:summary", default="", namespaces=ATOM_NS) or "", 500)
        cats = [
            c.attrib.get("term", "")
            for c in entry.findall("a:category", ATOM_NS)
            if c.attrib.get("term")
        ]
        out.append(
            {
                "id": aid,
                "title": title,
                "abstract": abstract,
                "categories": cats,
                "published": pub_dt.date().isoformat(),
                "matched_query": query,
            }
        )
    return out


def fetch_hn(since: datetime) -> list[dict]:
    ts = int(since.timestamp())
    url = (
        "https://hn.algolia.com/api/v1/search_by_date?"
        + urllib.parse.urlencode(
            {
                "query": "arxiv.org",
                "tags": "story",
                "numericFilters": f"created_at_i>{ts}",
                "hitsPerPage": "100",
            }
        )
    )
    raw = json.loads(_get(url).decode("utf-8"))
    out: list[dict] = []
    for hit in raw.get("hits", []):
        blob = " ".join(
            str(hit.get(k, "")) for k in ("url", "title", "story_text", "comment_text")
        )
        aid = _norm_id(blob)
        if not aid:
            continue
        out.append(
            {
                "id": aid,
                "title": _truncate(hit.get("title") or "", 300),
                "hn_points": int(hit.get("points") or 0),
                "hn_comments": int(hit.get("num_comments") or 0),
            }
        )
    return out


def fetch_hf(since: datetime) -> list[dict]:
    url = "https://huggingface.co/api/daily_papers"
    raw = json.loads(_get(url).decode("utf-8"))
    out: list[dict] = []
    cutoff = since.date()
    for item in raw:
        paper = item.get("paper") or {}
        aid = paper.get("id") or item.get("id") or ""
        aid = _norm_id(aid) or _norm_id(json.dumps(item))
        if not aid:
            continue
        pub = (item.get("publishedAt") or paper.get("publishedAt") or "")[:10]
        try:
            if pub and datetime.strptime(pub, "%Y-%m-%d").date() < cutoff:
                continue
        except ValueError:
            pass
        upvotes = int(paper.get("upvotes") or item.get("upvotes") or 0)
        title = _truncate(paper.get("title") or item.get("title") or "", 300)
        out.append({"id": aid, "title": title, "hf_upvotes": upvotes})
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--queries", nargs="+", required=True, help="arXiv query strings")
    p.add_argument("--max", type=int, default=40, help="max papers to emit")
    p.add_argument("--days", type=int, default=7, help="lookback window in days")
    args = p.parse_args()

    ensure_state()
    seen_path = scribe_home() / "seen.json"
    try:
        seen = json.loads(seen_path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        seen = {}

    since = datetime.now(timezone.utc) - timedelta(days=args.days)

    # Merge by id.
    merged: dict[str, dict] = {}

    for q in args.queries:
        try:
            for paper in fetch_arxiv(q, since):
                aid = paper["id"]
                entry = merged.setdefault(
                    aid,
                    {
                        "id": aid,
                        "title": paper["title"],
                        "abstract": paper["abstract"],
                        "categories": paper["categories"],
                        "published": paper["published"],
                        "signals": {
                            "hn_points": 0,
                            "hn_comments": 0,
                            "hf_upvotes": 0,
                            "matched_queries": [],
                        },
                    },
                )
                if not entry.get("abstract") and paper.get("abstract"):
                    entry["abstract"] = paper["abstract"]
                if not entry.get("categories") and paper.get("categories"):
                    entry["categories"] = paper["categories"]
                if not entry.get("published") and paper.get("published"):
                    entry["published"] = paper["published"]
                if q not in entry["signals"]["matched_queries"]:
                    entry["signals"]["matched_queries"].append(q)
        except Exception as e:  # noqa: BLE001
            print(f"scribe: arxiv query {q!r} failed: {e}", file=sys.stderr)

    try:
        for hit in fetch_hn(since):
            aid = hit["id"]
            entry = merged.setdefault(
                aid,
                {
                    "id": aid,
                    "title": hit.get("title") or "",
                    "abstract": "",
                    "categories": [],
                    "published": "",
                    "signals": {
                        "hn_points": 0,
                        "hn_comments": 0,
                        "hf_upvotes": 0,
                        "matched_queries": [],
                    },
                },
            )
            entry["signals"]["hn_points"] = max(
                entry["signals"]["hn_points"], hit.get("hn_points", 0)
            )
            entry["signals"]["hn_comments"] = max(
                entry["signals"]["hn_comments"], hit.get("hn_comments", 0)
            )
            if not entry.get("title") and hit.get("title"):
                entry["title"] = hit["title"]
    except Exception as e:  # noqa: BLE001
        print(f"scribe: hn fetch failed: {e}", file=sys.stderr)

    try:
        for hit in fetch_hf(since):
            aid = hit["id"]
            entry = merged.setdefault(
                aid,
                {
                    "id": aid,
                    "title": hit.get("title") or "",
                    "abstract": "",
                    "categories": [],
                    "published": "",
                    "signals": {
                        "hn_points": 0,
                        "hn_comments": 0,
                        "hf_upvotes": 0,
                        "matched_queries": [],
                    },
                },
            )
            entry["signals"]["hf_upvotes"] = max(
                entry["signals"]["hf_upvotes"], hit.get("hf_upvotes", 0)
            )
            if not entry.get("title") and hit.get("title"):
                entry["title"] = hit["title"]
    except Exception as e:  # noqa: BLE001
        print(f"scribe: hf fetch failed: {e}", file=sys.stderr)

    # Drop seen.
    candidates = [p for aid, p in merged.items() if aid not in seen]

    def rank_key(p: dict) -> tuple:
        s = p["signals"]
        sources = (
            (1 if s["matched_queries"] else 0)
            + (1 if s["hn_points"] or s["hn_comments"] else 0)
            + (1 if s["hf_upvotes"] else 0)
        )
        signal_strength = s["hn_points"] + 2 * s["hf_upvotes"] + s["hn_comments"] // 2
        return (-sources, -signal_strength, p.get("published", ""))

    candidates.sort(key=rank_key)
    out = candidates[: args.max]
    for paper in out:
        sys.stdout.write(json.dumps(paper, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
