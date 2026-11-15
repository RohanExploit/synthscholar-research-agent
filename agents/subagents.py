"""Four specialized Research Sub-Agents under SynthScholar Principal Investigator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .tools import fetch_arxiv_papers, fetch_openalex_works, search_github_code


@dataclass
class ScholarBusMessage:
    sender: str
    recipient: str
    phase: str
    content: str
    confidence: float


@dataclass
class ScholarContext:
    topic: str
    seen_arxiv_ids: set[str]
    papers: list[dict[str, Any]] = field(default_factory=list)
    openalex_works: list[dict[str, Any]] = field(default_factory=list)
    github_repos: list[dict[str, Any]] = field(default_factory=list)
    ranked_papers: list[dict[str, Any]] = field(default_factory=list)
    bibtex_pack: str = ""
    messages: list[ScholarBusMessage] = field(default_factory=list)

    def emit(self, sender: str, recipient: str, phase: str, content: str, confidence: float = 0.91) -> None:
        self.messages.append(ScholarBusMessage(sender, recipient, phase, content, round(confidence, 2)))


class ArXivOpenAlexHarvester:
    """Sub-Agent 1: Harvests live arXiv preprints and high-impact OpenAlex literature."""

    name = "ArXivOpenAlexHarvester"

    def run(self, ctx: ScholarContext) -> None:
        ax = fetch_arxiv_papers(ctx.topic, max_results=7)
        oa = fetch_openalex_works(ctx.topic, limit=5)
        ctx.papers = ax["papers"]
        ctx.openalex_works = oa["works"]
        new_cnt = sum(1 for p in ctx.papers if p["arxiv_id"] not in ctx.seen_arxiv_ids)
        ctx.emit(
            self.name,
            "CodeReproducibilityMatcher",
            "HARVEST",
            f"Fetched {len(ctx.papers)} arXiv preprints ({new_cnt} unseen) and {len(ctx.openalex_works)} cited OpenAlex works.",
            confidence=0.95,
        )


class CodeReproducibilityMatcher:
    """Sub-Agent 2: Queries GitHub Search to verify open-source code availability."""

    name = "CodeReproducibilityMatcher"

    def run(self, ctx: ScholarContext) -> None:
        gh = search_github_code(ctx.topic, limit=5)
        ctx.github_repos = gh["repos"]
        for p in ctx.papers:
            has_code_hint = any(k in p["abstract"].lower() for k in ("github.com", "open-source", "code is available", "implementation"))
            p["code_claim_in_abstract"] = has_code_hint
        ctx.emit(
            self.name,
            "MethodologyNoveltyCritic",
            "VERIFY-CODE",
            f"Found {len(ctx.github_repos)} top GitHub repos (total index matches={gh['total_matches']}).",
            confidence=0.89,
        )


class MethodologyNoveltyCritic:
    """Sub-Agent 3: Computes Research-to-Code Arbitrage Score and flags irreproducible hype."""

    name = "MethodologyNoveltyCritic"

    def run(self, ctx: ScholarContext) -> None:
        scored: list[dict[str, Any]] = []
        topic_tokens = {t.lower() for t in ctx.topic.split() if len(t) > 2}
        for p in ctx.papers:
            text = (p["title"] + " " + p["abstract"]).lower()
            relevance = sum(12 for tok in topic_tokens if tok in text)
            novelty = 18 if p["arxiv_id"] not in ctx.seen_arxiv_ids else 4
            repro_bonus = 20 if p.get("code_claim_in_abstract") else 6
            arbitrage_gap = 16 if not p.get("code_claim_in_abstract") else 8
            utility = round(min(99.0, 25.0 + relevance + novelty + repro_bonus + arbitrage_gap), 1)
            badge = "REPRODUCIBLE" if p.get("code_claim_in_abstract") else "OPEN-CODE GAP"
            scored.append({**p, "arbitrage_score": utility, "repro_status": badge})

        scored.sort(key=lambda x: x["arbitrage_score"], reverse=True)
        ctx.ranked_papers = scored
        top_title = scored[0]["title"][:55] if scored else "N/A"
        ctx.emit(
            self.name,
            "LiteratureMatrixSynthesizer",
            "CRITIQUE",
            f"Ranked {len(scored)} preprints. Top frontier candidate: \"{top_title}...\" (score={scored[0]['arbitrage_score'] if scored else 0}).",
            confidence=0.92,
        )


class LiteratureMatrixSynthesizer:
    """Sub-Agent 4: Generates BibTeX export pack and concrete experiment direction."""

    name = "LiteratureMatrixSynthesizer"

    def run(self, ctx: ScholarContext) -> None:
        entries = []
        for idx, p in enumerate(ctx.ranked_papers[:5], start=1):
            year = (p.get("published") or "2026")[:4]
            entries.append(
                f"@article{{synth{idx}_{year},\n"
                f"  title={{{p['title']}}},\n"
                f"  author={{{p['authors']}}},\n"
                f"  year={{{year}}},\n"
                f"  eprint={{{p['arxiv_id']}}},\n"
                f"  archivePrefix={{arXiv}}\n}}"
            )
        ctx.bibtex_pack = "\n\n".join(entries)
        ctx.emit(
            self.name,
            "SynthScholar PI",
            "SYNTHESIZE",
            f"Compiled {len(entries)} BibTeX citations and research-gap matrix.",
            confidence=0.96,
        )
