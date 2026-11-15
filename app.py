"""SynthScholar — Warm Academic Studio UI with Live n8n Research Workflow."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from agents.orchestrator import SynthScholarPI
from agents.workflow_viz import render_n8n_workflow

st.set_page_config(
    page_title="SynthScholar | Autonomous Research Arbitrage Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

TOPICS = {
    "Agentic AI & Tool Use": "agentic ai tool use",
    "Multi-Agent Reinforcement Learning": "multi agent reinforcement learning",
    "Protein Structure Diffusion Models": "protein folding diffusion",
    "Graph Neural Networks in Drug Discovery": "graph neural network drug discovery",
}

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,700&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1C1917; }
h1, h2, h3, .serif-title { font-family: 'Newsreader', serif !important; }
code, pre, .mono { font-family: 'JetBrains Mono', monospace !important; }
.stApp { background-color: #FBF9F5; }
.journal-masthead { border-top: 3px solid #1C1917; border-bottom: 1px solid #D6D3CD; padding: 0.9rem 0.2rem; margin-bottom: 0.9rem; }
.kpi-warm { background:#FFFFFF; border:1px solid #E7E2D8; border-radius:10px; padding:0.8rem 1rem; transition:transform .2s ease; }
.kpi-warm:hover { transform: translateY(-2px); border-color:#9A3412; }
</style>
""",
    unsafe_allow_html=True,
)

if "sch_topic" not in st.session_state:
    st.session_state.sch_topic = "agentic ai tool use"


def _apply_topic() -> None:
    st.session_state.sch_topic = TOPICS[st.session_state.sch_sample]
    st.session_state.sch_force = True


with st.sidebar:
    st.markdown("### Sample Research Frontiers")
    st.selectbox("Load Sample Domain", list(TOPICS.keys()), key="sch_sample", on_change=_apply_topic)
    st.markdown("### Query Configuration")
    topic_in = st.text_input("Research Topic / Keywords", key="sch_topic")
    with st.expander("AI Brain Keys (Optional)"):
        gemini_key = st.text_input("Gemini API Key Override", type="password")
        groq_key = st.text_input("Groq API Key Override", type="password")
    run_btn = st.button("Harvest & Score Frontier", type="primary", width="stretch")
    st.caption("Sanket Autade · BTCOC701")

if "scholar_res" not in st.session_state or run_btn or st.session_state.pop("sch_force", False):
    with st.spinner("Harvester fetching arXiv, OpenAlex & GitHub repositories..."):
        st.session_state.scholar_res = SynthScholarPI().run_harvest(
            topic=topic_in,
            gemini_key=gemini_key,
            groq_key=groq_key,
        )

res = st.session_state.scholar_res
papers_df = pd.DataFrame(res["ranked_papers"])
msgs = res["messages"]

st.markdown(
    f"""
<div class="journal-masthead">
  <div style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:0.6rem;">
    <div>
      <h1 class="serif-title" style="margin:0; font-size:1.95rem; color:#1C1917;">SynthScholar — Research &amp; Code Arbitrage</h1>
      <div class="mono" style="color:#57534E; font-size:0.8rem;">arXiv Atom XML · OpenAlex Citation Graph · GitHub Repo Matcher · BibTeX</div>
    </div>
    <div class="mono" style="color:#0F766E; font-weight:700; font-size:0.86rem;">TOPIC: {res['topic'].upper()}</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="kpi-warm"><div style="font-size:0.72rem;color:#78716C;">ARXIV PREPRINTS</div><div style="font-size:1.45rem;font-weight:700;">{len(papers_df)}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="kpi-warm"><div style="font-size:0.72rem;color:#78716C;">OPENALEX CITATIONS</div><div style="font-size:1.45rem;font-weight:700;">{len(res["openalex_works"])}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="kpi-warm"><div style="font-size:0.72rem;color:#78716C;">GITHUB CODE REPOS</div><div style="font-size:1.45rem;font-weight:700;color:#0F766E;">{len(res["github_repos"])}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="kpi-warm"><div style="font-size:0.72rem;color:#78716C;">AI ENGINE</div><div style="font-size:1.05rem;font-weight:700;padding-top:0.2rem;">{res["synthesis"]["model"]}</div></div>', unsafe_allow_html=True)

st.markdown("")
wf_nodes = [
    {"title": "SynthScholar PI", "role": "Orchestrator", "phase": "TRIGGER", "metric": res["topic"][:18], "payload": f"Loaded {len(res['memory'].get('seen_arxiv_ids', []))} seen arXiv IDs from memory", "confidence": 0.98, "color": "#9A3412", "icon": "📚"},
    {"title": "ArXivOpenAlexScout", "role": "Scout 1", "phase": "HARVEST", "metric": f"{len(papers_df)} papers", "payload": msgs[0]["content"] if len(msgs) > 0 else "Queried arXiv + OpenAlex", "confidence": msgs[0]["confidence"] if len(msgs) > 0 else 0.94, "color": "#B45309", "icon": "📄"},
    {"title": "CodeRepoMatcher", "role": "Scout 2", "phase": "GITHUB", "metric": f"{len(res['github_repos'])} repos", "payload": msgs[1]["content"] if len(msgs) > 1 else "Matched GitHub codebases", "confidence": msgs[1]["confidence"] if len(msgs) > 1 else 0.91, "color": "#0F766E", "icon": "💻"},
    {"title": "NoveltyGapCritic", "role": "Critic", "phase": "SCORE", "metric": f"Top {int(papers_df['arbitrage_score'].max()) if not papers_df.empty else 0}/100", "payload": msgs[2]["content"] if len(msgs) > 2 else "Tagged OPEN-CODE GAP vs REPRODUCIBLE", "confidence": msgs[2]["confidence"] if len(msgs) > 2 else 0.92, "color": "#D97706", "icon": "⚖️"},
    {"title": "BibTeXSynthesizer", "role": "Planner", "phase": "COMPILE", "metric": "references.bib", "payload": msgs[3]["content"] if len(msgs) > 3 else "Compiled @article entries", "confidence": msgs[3]["confidence"] if len(msgs) > 3 else 0.95, "color": "#1C1917", "icon": "✍️"},
    {"title": "Paper Memory + Studio", "role": "Memory", "phase": "PERSIST", "metric": res["synthesis"]["provider"].split()[0], "payload": "Deduplicated harvest state saved", "confidence": 0.99, "color": "#0F766E", "icon": "💾"},
]
render_n8n_workflow(
    wf_nodes,
    theme={"mode": "light", "bg": "#F3EFE6", "card_bg": "#FFFFFF", "border": "#D6D3CD", "accent": "#9A3412", "text": "#1C1917", "muted": "#57534E", "bar_bg": "#FFFFFF"},
    engine_label=f"SynthScholar Research DAG · {res['synthesis']['provider']}",
)

t_lit, t_code, t_peas = st.tabs(["Arbitrage Charts & Preprints Matrix", "GitHub Baselines & BibTeX", "Agent Bus & Memory"])

with t_lit:
    c1, c2 = st.columns([1.3, 1])
    with c1:
        if not papers_df.empty:
            fig = px.bar(papers_df, x="arxiv_id", y="arbitrage_score", color="repro_status", color_discrete_map={"REPRODUCIBLE": "#0F766E", "OPEN-CODE GAP": "#9A3412"}, hover_data=["title"], title="Research-to-Code Arbitrage Score")
            fig.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FBF9F5", height=300, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig, width="stretch")
    with c2:
        oa_df = pd.DataFrame(res["openalex_works"])
        if not oa_df.empty:
            fig_oa = px.bar(oa_df.head(6), x="cited_by", y="year", orientation="h", color="open_access", hover_data=["title"], title="OpenAlex Foundational Citation Impact")
            fig_oa.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FBF9F5", height=300, margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(fig_oa, width="stretch")

    if not papers_df.empty:
        st.dataframe(
            papers_df[["arxiv_id", "title", "published", "repro_status", "arbitrage_score", "url"]],
            width="stretch",
            hide_index=True,
            column_config={
                "arbitrage_score": st.column_config.ProgressColumn("Arbitrage Score", min_value=0, max_value=100, format="%d/100"),
                "url": st.column_config.LinkColumn("arXiv Link", display_text="Open Paper"),
            },
        )
    with st.expander(f"Principal Investigator Brief ({res['synthesis']['provider']})", expanded=False):
        st.write(res["synthesis"]["text"])

with t_code:
    c_gh, c_bib = st.columns([1, 1])
    with c_gh:
        st.markdown("#### Matched Open-Source Repositories")
        gh_df = pd.DataFrame(res["github_repos"])
        if not gh_df.empty:
            fig_gh = px.bar(gh_df, x="repo", y="stars", color="language", title="Repository Traction (GitHub Stars)", height=250)
            fig_gh.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#FBF9F5")
            st.plotly_chart(fig_gh, width="stretch")
            st.dataframe(gh_df, width="stretch", hide_index=True, column_config={"url": st.column_config.LinkColumn("GitHub")})
    with c_bib:
        st.markdown("#### Compiled BibTeX Export")
        st.code(res["bibtex_pack"], language="bibtex")
        st.download_button("Download references.bib", data=res["bibtex_pack"], file_name="references.bib", width="stretch")

with t_peas:
    mdf = pd.DataFrame(msgs)
    if not mdf.empty:
        st.plotly_chart(px.bar(mdf, x="sender", y="confidence", color="phase", title="Sub-Agent Confidence", height=240).update_layout(paper_bgcolor="#FFFFFF"), width="stretch")
        st.dataframe(mdf[["phase", "sender", "recipient", "confidence", "content"]], width="stretch", hide_index=True)
    if res["memory"].get("harvest_history"):
        st.dataframe(pd.DataFrame(res["memory"]["harvest_history"]), width="stretch", hide_index=True)
    st.table(pd.DataFrame([{"PEAS": "P", "Spec": "Novelty-vs-code recall & valid BibTeX"}, {"PEAS": "E", "Spec": "arXiv Atom, OpenAlex, GitHub Search"}, {"PEAS": "A", "Spec": "Arbitrage Matrix, BibTeX Pack, Paper Memory"}, {"PEAS": "S", "Spec": "arXiv XML, Citation counts, Repo stars"}]))
