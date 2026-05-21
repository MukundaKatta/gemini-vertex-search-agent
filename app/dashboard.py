"""gemini-vertex-search-agent dashboard."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemini_vertex_search_agent.runner import ask  # noqa: E402


st.set_page_config(
    page_title="gemini-vertex-search-agent",
    layout="wide",
    page_icon=":mag:",
)
st.title("gemini-vertex-search-agent")
st.caption(
    "Enterprise document Q&A agent on Vertex AI Search + Gemini 2.5 + "
    "GenAI App Builder credits. Returns byte-for-byte verbatim citations "
    "from the indexed docs. Apache 2.0."
)

with st.sidebar:
    st.header("Search the docs")
    question = st.text_area(
        "Your question",
        value="how do I rotate the production database credentials",
        height=120,
    )
    model = st.selectbox(
        "Gemini model",
        options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"],
        index=0,
    )
    stub = st.toggle(
        "Use stub Vertex AI Search MCP",
        value=True,
        help=(
            "On = local stub with a canned engineering-docs-prod data store "
            "(3 runbooks). Off = real Vertex AI Search via "
            "google-cloud-discoveryengine (set GOOGLE_CLOUD_PROJECT + "
            "DATA_STORE_ID)."
        ),
    )
    run = st.button("Search docs", type="primary", use_container_width=True)
    st.divider()
    st.caption(
        f"Project: `{os.getenv('GOOGLE_CLOUD_PROJECT', 'not-set')}`  "
        f"Vertex AI: `{os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'true')}`"
    )

st.markdown(
    """
The agent walks these Vertex AI Search (Discovery Engine) tools to answer
plain-English doc-Q&A questions:
- **list_data_stores** to enumerate the indexed corpora
- **search** for the top ranked documents in a data store
- **get_document** to read the full indexed text before citing it verbatim
- **summarize_search** for a one-paragraph synthesis with citations
"""
)

if run:
    with st.status("Running Vertex AI Gemini...", expanded=True) as status:
        t0 = time.perf_counter()
        try:
            resp = ask(question, stub=stub, model=model)
        except Exception as e:  # pragma: no cover
            status.update(label=f"Error: {e}", state="error")
            st.exception(e)
            st.stop()
        elapsed = (time.perf_counter() - t0) * 1000
        status.update(label=f"Done in {elapsed:.0f} ms", state="complete")

    st.subheader("Answer")
    st.markdown(resp.final_text or "_(no final response)_")

    with st.expander(f"Agent event trace ({len(resp.events)} events)"):
        for i, ev in enumerate(resp.events):
            st.markdown(f"**{i}.** author=`{ev.get('author')}` final=`{ev.get('is_final')}`")
            text = ev.get("text") or ""
            if text:
                st.code(text[:1500], language=None)
else:
    st.info("Use the sidebar to ask a question against the stub Vertex AI Search data store.")
