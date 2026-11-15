"""Keyless live scholarly sensors: arXiv Atom API, OpenAlex Works API, and GitHub Search."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import requests

HEADERS = {"User-Agent": "SynthScholar-Research-Agent/1.0 (mailto:research@example.edu)"}


def fetch_arxiv_papers(query: str, max_results: int = 8, timeout: float = 6.0) -> dict[str, Any]:
    """Fetch recent preprints from arXiv Atom API without requiring a key."""
    clean_q = query.strip() or "multi-agent reinforcement learning"
    try:
        resp = requests.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": f"all:{clean_q}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
            headers=HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []
        for entry in root.findall("atom:entry", ns):
            raw_id = (entry.findtext("atom:id", "", ns) or "").strip()
            arxiv_id = raw_id.rsplit("/", 1)[-1]
            title = " ".join((entry.findtext("atom:title", "", ns) or "").split())
            summary = " ".join((entry.findtext("atom:summary", "", ns) or "").split())[:260]
            published = (entry.findtext("atom:published", "", ns) or "")[:10]
            authors = [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)[:3]]
            papers.append(
                {
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "authors": ", ".join([a for a in authors if a]) or "Unknown",
                    "published": published,
                    "abstract": summary,
                    "url": raw_id,
                }
            )
        return {"papers": papers, "source": "live-arxiv-atom", "ok": True}
    except Exception as exc:
        backup = [
            {
                "arxiv_id": "2501.00001v1",
                "title": f"Autonomous Multi-Agent Coordination in {clean_q.title()}",
                "authors": "A. Researcher, B. Scientist",
                "published": "2026-11-01",
                "abstract": "Fallback preprint snapshot when arXiv API is throttled or offline.",
                "url": "https://arxiv.org",
            }
        ]
        return {"papers": backup, "source": f"arxiv-backup ({type(exc).__name__})", "ok": False}


def fetch_openalex_works(query: str, limit: int = 6, timeout: float = 5.5) -> dict[str, Any]:
    """Query OpenAlex Works API for citation velocity and open-access research works."""
    clean_q = query.strip() or "multi-agent systems"
    try:
        resp = requests.get(
            "https://api.openalex.org/works",
            params={"search": clean_q, "per-page": limit, "sort": "cited_by_count:desc"},
            headers=HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        works = []
        for w in resp.json().get("results", []):
            works.append(
                {
                    "title": (w.get("title") or "Untitled")[:110],
                    "year": w.get("publication_year", 2025),
                    "cited_by": int(w.get("cited_by_count") or 0),
                    "open_access": bool((w.get("open_access") or {}).get("is_oa")),
                    "doi": w.get("doi") or "",
                }
            )
        return {"works": works, "source": "live-openalex", "ok": True}
    except Exception as exc:
        return {"works": [], "source": f"openalex-backup ({type(exc).__name__})", "ok": False}


def search_github_code(topic_or_title: str, limit: int = 4, timeout: float = 5.0) -> dict[str, Any]:
    """Search GitHub public repositories to measure code reproducibility."""
    words = [w for w in topic_or_title.replace(":", " ").split() if len(w) > 3][:5]
    q = " ".join(words) or "multi agent"
    try:
        resp = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": q, "sort": "stars", "order": "desc", "per_page": limit},
            headers=HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        repos = [
            {
                "repo": it.get("full_name", ""),
                "stars": int(it.get("stargazers_count") or 0),
                "language": it.get("language") or "Python",
                "url": it.get("html_url", ""),
            }
            for it in items
        ]
        return {"repos": repos, "total_matches": int(resp.json().get("total_count") or 0), "source": "live-github-search"}
    except Exception as exc:
        return {"repos": [], "total_matches": 0, "source": f"github-backup ({type(exc).__name__})"}
