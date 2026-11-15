"""Lead SynthScholar Principal Investigator orchestrating research & code arbitrage."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .llm_router import SynthesisResult, synthesize_with_fallback
from .memory import PaperMemoryStore
from .subagents import (
    ArXivOpenAlexHarvester,
    CodeReproducibilityMatcher,
    LiteratureMatrixSynthesizer,
    MethodologyNoveltyCritic,
    ScholarContext,
)


def _universal_scholar_fallback(ctx: ScholarContext) -> str:
    top_p = ctx.ranked_papers[0] if ctx.ranked_papers else {}
    top_oa = ctx.openalex_works[0] if ctx.openalex_works else {}
    top_repo = ctx.github_repos[0] if ctx.github_repos else {}
    return (
        f"### SynthScholar Frontier Research Brief: `{ctx.topic}`\n"
        f"- **Top Newly Harvested Preprint**: *{top_p.get('title', 'N/A')}* (`{top_p.get('arxiv_id', '')}`, Arbitrage Score `{top_p.get('arbitrage_score', 0)}/100`, Status: `{top_p.get('repro_status', '')}`).\n"
        f"- **Citation Anchor (OpenAlex)**: *{top_oa.get('title', 'No OpenAlex anchor')}* ({top_oa.get('cited_by', 0)} citations).\n"
        f"- **Code Reproducibility**: Top GitHub reference `{top_repo.get('repo', 'None found')}` ({top_repo.get('stars', 0)}★). "
        f"Opportunity: benchmark this paper's core mechanism against the open-source baseline."
    )


class SynthScholarPI:
    """Goal-Based + Model-Based + Utility-Based Research Arbitrage Agent."""

    def __init__(self, memory_store: PaperMemoryStore | None = None) -> None:
        self.memory = memory_store or PaperMemoryStore()
        self.subagents = [
            ArXivOpenAlexHarvester(),
            CodeReproducibilityMatcher(),
            MethodologyNoveltyCritic(),
            LiteratureMatrixSynthesizer(),
        ]

    def run_harvest(
        self,
        topic: str = "agentic ai tool use",
        gemini_key: str | None = None,
        groq_key: str | None = None,
    ) -> dict[str, Any]:
        state = self.memory.load()
        ctx = ScholarContext(topic=topic.strip() or "agentic ai tool use", seen_arxiv_ids=set(state.get("seen_arxiv_ids", [])))
        ctx.emit(
            "SynthScholar PI",
            "ArXivOpenAlexHarvester",
            "DELEGATE",
            f"Launching autonomous literature & GitHub reproducibility arbitrage for `{ctx.topic}`.",
            confidence=0.98,
        )

        for agent in self.subagents:
            agent.run(ctx)

        top_score = ctx.ranked_papers[0]["arbitrage_score"] if ctx.ranked_papers else 0.0
        prompt = (
            f"You are SynthScholar Principal Investigator. Synthesize a crisp 3-bullet research opportunity brief "
            f"(Breakthrough Signal, Reproducibility Gap, Concrete Next Experiment) under 115 words for topic '{ctx.topic}'.\n"
            f"Top Preprints: {ctx.ranked_papers[:3]}\nTop Repos: {ctx.github_repos[:3]}"
        )
        synthesis: SynthesisResult = synthesize_with_fallback(
            prompt=prompt,
            system_instruction="Be scholarly, rigorous, and cite only provided titles/IDs.",
            universal_fallback_fn=lambda: _universal_scholar_fallback(ctx),
            gemini_key=gemini_key,
            groq_key=groq_key,
        )

        updated_state = self.memory.update_after_harvest(
            topic=ctx.topic,
            arxiv_ids=[p["arxiv_id"] for p in ctx.ranked_papers],
            top_utility=top_score,
            summary=synthesis.text,
        )

        return {
            "topic": ctx.topic,
            "ranked_papers": ctx.ranked_papers,
            "openalex_works": ctx.openalex_works,
            "github_repos": ctx.github_repos,
            "bibtex_pack": ctx.bibtex_pack,
            "messages": [asdict(m) for m in ctx.messages],
            "synthesis": asdict(synthesis),
            "memory": updated_state,
        }
