"""Headless autonomous runner for scheduled SynthScholar arXiv + OpenAlex frontier scans."""

from __future__ import annotations

import json
import os

from agents.orchestrator import SynthScholarPI


def main() -> None:
    topic = os.environ.get("SCHOLAR_TOPIC", "agentic ai tool use")
    res = SynthScholarPI().run_harvest(topic=topic)
    print(
        json.dumps(
            {
                "topic": res["topic"],
                "papers_ranked": len(res["ranked_papers"]),
                "github_repos": len(res["github_repos"]),
                "provider": res["synthesis"]["provider"],
                "total_harvests": res["memory"]["total_harvests"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
