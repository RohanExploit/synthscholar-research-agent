"""Automated pytest suite for SynthScholar multi-agent research arbitrage system."""

from __future__ import annotations

from pathlib import Path

from agents.memory import PaperMemoryStore
from agents.orchestrator import SynthScholarPI
from agents.subagents import MethodologyNoveltyCritic, ScholarContext


def test_paper_memory_deduplicates_ids(tmp_path: Path) -> None:
    store = PaperMemoryStore(tmp_path / "papers.json")
    s1 = store.update_after_harvest("agents", ["2601.001", "2601.002"], 82.0, "ok")
    s2 = store.update_after_harvest("agents", ["2601.002", "2601.003"], 88.0, "ok2")
    assert s1["seen_arxiv_ids"] == ["2601.001", "2601.002"]
    assert s2["seen_arxiv_ids"] == ["2601.001", "2601.002", "2601.003"]
    assert s2["total_harvests"] == 2


def test_novelty_critic_ranks_reproducible_higher() -> None:
    critic = MethodologyNoveltyCritic()
    ctx = ScholarContext(
        topic="agentic tool",
        seen_arxiv_ids=set(),
        papers=[
            {"arxiv_id": "1", "title": "Agentic Tool Use", "abstract": "github.com code is available", "code_claim_in_abstract": True},
            {"arxiv_id": "2", "title": "Unrelated Note", "abstract": "no implementation", "code_claim_in_abstract": False},
        ],
    )
    critic.run(ctx)
    assert ctx.ranked_papers[0]["arxiv_id"] == "1"
    assert ctx.ranked_papers[0]["repro_status"] == "REPRODUCIBLE"


def test_full_harvest_mocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "agents.subagents.fetch_arxiv_papers",
        lambda q, max_results=7: {"papers": [{"arxiv_id": "2611.1234", "title": "Multi-Agent Planner", "authors": "S. Autade", "published": "2026-11-10", "abstract": "open-source github.com/test"}], "source": "mock", "ok": True},
    )
    monkeypatch.setattr(
        "agents.subagents.fetch_openalex_works",
        lambda q, limit=5: {"works": [{"title": "Foundational Agent Work", "year": 2024, "cited_by": 150, "open_access": True, "doi": ""}], "source": "mock", "ok": True},
    )
    monkeypatch.setattr(
        "agents.subagents.search_github_code",
        lambda topic, limit=5: {"repos": [{"repo": "org/agent", "stars": 420, "language": "Python", "url": "https://github.com/org/agent"}], "total_matches": 1, "source": "mock"},
    )
    out = SynthScholarPI(PaperMemoryStore(tmp_path / "papers.json")).run_harvest("multi agent", gemini_key="", groq_key="")
    assert len(out["messages"]) == 5
    assert "@article{synth1_2026" in out["bibtex_pack"]
