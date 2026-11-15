"""SynthScholar — Warm Academic Archival Studio UI."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from agents.orchestrator import SynthScholarPI

st.set_page_config(
    page_title="SynthScholar | Autonomous Research Arbitrage Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,700&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1C1917; }
h1, h2, h3, .serif-title { font-family: 'Newsreader', serif !important; }
code, pre, .mono { font-family: 'JetBrains Mono', monospace !important; }
.stApp { background-color: #FBF9F5; }
.journal-masthead {
    border-top: 3px solid #1C1917;
    border-bottom: 1px solid #D6D3CD;
    padding: 1.1rem 0.2rem;
    margin-bottom: 1.1rem;
}
.scholar-card {
    background: #FFFFFF;
    border: 1px solid #E7E2D8;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.7rem;
}
.bus-note {
    background: #F3EFE6;
    border-left: 4px solid #9A3412;
    padding: 0.7rem 1rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 0.55rem;
}
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Research Frontier Query")
    topic_in = st.text_input("Research Topic / Keywords", value="agentic ai tool use")
    with st.expander("AI Brain Keys (Optional — 90% Keyless)"):
        gemini_key = st.text_input("Gemini API Key Override", type="password")
        groq_key = st.text_input("Groq API Key Override", type="password")
    run_btn = st.button("Harvest & Score Frontier", type="primary", use_container_width=True)
    st.caption("Built by Sanket Autade | BTCOC701 CAS Activity-I")

if "scholar_res" not in st.session_state or run_btn:
    with st.spinner("SynthScholar coordinating arXiv, OpenAlex & GitHub reproducibility sub-agents..."):
        st.session_state.scholar_res = SynthScholarPI().run_harvest(
            topic=topic_in,
            gemini_key=gemini_key,
            groq_key=groq_key,
        )

res = st.session_state.scholar_res
papers_df = pd.DataFrame(res["ranked_papers"])

st.markdown(
    f"""
<div class="journal-masthead">
  <div style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:0.8rem;">
    <div>
      <h1 class="serif-title" style="margin:0; font-size:2.1rem; color:#1C1917;">SynthScholar — Research &amp; Code Arbitrage Workbench</h1>
      <div style="color:#57534E; margin-top:0.2rem;">Autonomous cross-synthesis across arXiv Atom Preprints, OpenAlex Citations &amp; GitHub Open-Source Repositories</div>
    </div>
    <div class="mono" style="color:#0F766E; font-weight:600; font-size:0.86rem;">TOPIC: {res['topic']}</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("arXiv Preprints", len(papers_df))
m2.metric("OpenAlex Anchors", len(res["openalex_works"]))
m3.metric("GitHub Repos Matched", len(res["github_repos"]))
m4.metric("10% AI Synthesizer", res["synthesis"]["provider"])

t_lit, t_bus, t_peas = st.tabs(["Frontier Matrix & BibTeX", "Sub-Agent Scholarly Bus", "PEAS & Harvest Memory"])

with t_lit:
    col_a, col_b = st.columns([1.3, 1])
    with col_a:
        st.subheader("Ranked Preprints by Research-to-Code Arbitrage Score")
        if not papers_df.empty:
            fig = px.bar(
                papers_df,
                x="arxiv_id",
                y="arbitrage_score",
                color="repro_status",
                color_discrete_map={"REPRODUCIBLE": "#0F766E", "OPEN-CODE GAP": "#9A3412"},
                hover_data=["title"],
                height=290,
            )
            fig.update_layout(paper_bgcolor="#FBF9F5", plot_bgcolor="#FFFFFF", margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)

            for _, row in papers_df.head(5).iterrows():
                st.markdown(
                    f"""
<div class="scholar-card">
  <div class="mono" style="font-size:0.75rem; color:#9A3412;">arXiv:{row['arxiv_id']} · {row['published']} · {row['repro_status']} · Score {row['arbitrage_score']}/100</div>
  <div style="font-weight:700; font-size:1.02rem; margin-top:0.2rem;"><a href="{row['url']}" target="_blank" style="color:#1C1917; text-decoration:none;">{row['title']}</a></div>
  <div style="font-size:0.84rem; color:#57534E; margin-top:0.2rem;">{row['authors']}</div>
  <div style="font-size:0.88rem; color:#292524; margin-top:0.35rem;">{row['abstract']}...</div>
</div>
""",
                    unsafe_allow_html=True,
                )

    with col_b:
        st.subheader("Principal Investigator Synthesis")
        st.success(res["synthesis"]["text"])
        st.subheader("Matched Open-Source GitHub Baselines")
        if res["github_repos"]:
            st.dataframe(pd.DataFrame(res["github_repos"]), use_container_width=True, hide_index=True)
        st.subheader("Auto-Compiled BibTeX Pack")
        st.code(res["bibtex_pack"], language="bibtex")
        st.download_button("Download references.bib", data=res["bibtex_pack"], file_name="references.bib", use_container_width=True)

with t_bus:
    st.subheader("Sub-Agent Scholarly Coordination Bus")
    for m in res["messages"]:
        st.markdown(
            f'<div class="bus-note"><div class="mono" style="font-size:0.78rem; color:#9A3412;">[{m["phase"]}] {m["sender"]} → {m["recipient"]} (conf={m["confidence"]})</div><div style="margin-top:0.2rem;">{m["content"]}</div></div>',
            unsafe_allow_html=True,
        )

with t_peas:
    st.subheader("PEAS Agent Architecture")
    st.table(
        pd.DataFrame(
            [
                {"Component": "P — Performance Measure", "Description": "Novelty-vs-reproducibility detection accuracy, zero duplicate preprint alerts, valid BibTeX synthesis."},
                {"Component": "E — Environment", "Description": "arXiv Atom repository, OpenAlex citation graph, GitHub code index, Streamlit Cloud & GitHub Actions."},
                {"Component": "A — Actuators", "Description": "Ranked frontier matrix, BibTeX compiler, deduplicated arXiv memory updater."},
                {"Component": "S — Sensors", "Description": "arXiv XML feeds, OpenAlex JSON works, GitHub repository search, state/paper_memory.json."},
            ]
        )
    )
    if res["memory"].get("harvest_history"):
        st.dataframe(pd.DataFrame(res["memory"]["harvest_history"]), use_container_width=True, hide_index=True)
