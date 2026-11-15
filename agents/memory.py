"""Model-based persistent memory for SynthScholar deduplicated arXiv & OpenAlex harvests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATE: dict[str, Any] = {
    "agent_name": "SynthScholar Principal Investigator",
    "seen_arxiv_ids": [],
    "harvest_history": [],
    "total_harvests": 0,
    "last_harvest_utc": None,
}


class PaperMemoryStore:
    """Tracks deduplicated arXiv paper IDs and historical frontier briefs."""

    def __init__(self, state_path: Path | str | None = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.path = Path(state_path) if state_path else base_dir / "state" / "paper_memory.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return json.loads(json.dumps(DEFAULT_STATE))
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for key, val in DEFAULT_STATE.items():
                data.setdefault(key, json.loads(json.dumps(val)))
            return data
        except Exception:
            return json.loads(json.dumps(DEFAULT_STATE))

    def save(self, state: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def update_after_harvest(
        self,
        topic: str,
        arxiv_ids: list[str],
        top_utility: float,
        summary: str,
    ) -> dict[str, Any]:
        state = self.load()
        seen = set(state.get("seen_arxiv_ids", []))
        new_ids = [aid for aid in arxiv_ids if aid not in seen]
        state["seen_arxiv_ids"] = (state.get("seen_arxiv_ids", []) + new_ids)[-300:]

        now_iso = datetime.now(timezone.utc).isoformat()
        state["total_harvests"] = int(state.get("total_harvests", 0)) + 1
        state["last_harvest_utc"] = now_iso
        state["harvest_history"].append(
            {
                "timestamp_utc": now_iso,
                "topic": topic,
                "papers_processed": len(arxiv_ids),
                "new_papers": len(new_ids),
                "top_arbitrage_score": round(top_utility, 1),
                "summary": summary[:200],
            }
        )
        state["harvest_history"] = state["harvest_history"][-30:]
        self.save(state)
        return state
