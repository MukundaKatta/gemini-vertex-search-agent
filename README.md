# gemini-vertex-search-agent

An enterprise document Q&A agent built on **Google Cloud Agent Builder
(ADK)**, **Gemini 2.5**, and **Vertex AI Search (Discovery Engine)**.

You ask a question in plain English ("how do I rotate the production
database credentials?"). The agent searches an indexed corpus of
engineering docs, reads the top-matching document, and answers with
byte-for-byte verbatim citations — every command, every path, every
number copied straight from the indexed source.

**Live demo:** https://gemini-vertex-search-agent-1029931682737.us-central1.run.app
**Demo video:** see `.video-build/demo.mp4`
**License:** Apache 2.0

## What it does

The agent walks the standard Vertex AI Search (Discovery Engine) tool
surface:

1. `list_data_stores` to enumerate the indexed corpora.
2. `search` against the chosen data store for the user's question.
3. `get_document` on the top hit to load the full indexed text.
4. (Optional) `summarize_search` for a one-paragraph synthesis with
   citations.

The answer is structured into five labeled sections — ANSWER, SOURCES,
KEY QUOTES, CONFIDENCE, NEXT STEP — and every command/path/number in
those sections is byte-for-byte from the retrieved doc. KEY QUOTES are
unedited. CONFIDENCE is tied to the top result's relevance score; if the
best result scores below 0.5 the agent flags it.

A stub Discovery Engine MCP server ships in the repo with a canned
`engineering-docs-prod` data store (3 runbooks: DB credential rotation,
Vault unseal, backup restore) so reviewers can reproduce the demo with
zero cloud setup.

## Architecture

```
┌─────────────┐  user question         ┌──────────────────────────────┐
│  Streamlit  │ ────────────────────▶  │  ADK LlmAgent (Gemini 2.5)   │
│  dashboard  │                         │  on Vertex AI                │
└─────────────┘ ◀── answer + cites ─── └────┬─────────────────────────┘
                                              │ MCPToolset / stdio
                                              │ or FunctionTool / SDK
                                              ▼
                                   ┌──────────────────────────────────┐
                                   │  Vertex AI Search                 │
                                   │  (Discovery Engine)               │
                                   │  stub by default,                 │
                                   │  real corpus via env vars         │
                                   └──────────────────────────────────┘
```

## Try it locally (stub mode)

```bash
git clone https://github.com/MukundaKatta/gemini-vertex-search-agent
cd gemini-vertex-search-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-project
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_LOCATION=us-central1

PYTHONPATH=src streamlit run app/dashboard.py
```

Ask the default question, "how do I rotate the production database
credentials", and the agent will quote the canned runbook verbatim.

## Try it against a real Vertex AI Search data store

The agent's `stub=False` path uses the
[`google-cloud-discoveryengine`](https://pypi.org/project/google-cloud-discoveryengine/)
Python SDK to call the real Discovery Engine API. Provide the project,
data store id, and (optionally) the location:

```bash
export GOOGLE_CLOUD_PROJECT=your-project
export DATA_STORE_ID=your-data-store-id
export DISCOVERY_ENGINE_LOCATION=global   # or "us" / "eu"
```

Untick **Use stub Vertex AI Search MCP** in the sidebar. The agent now
calls `DataStoreServiceClient`, `SearchServiceClient`, and
`DocumentServiceClient` directly against your indexed corpus — same
tool surface, same five-section labeled output, same verbatim-citation
rule.

## Tests

```bash
PYTHONPATH=src pytest -q
```

14 tests cover the stub server's responses, the search -> document
chain consistency (so the agent's citations stay verbatim), and the
agent wiring.

## Hackathons

This repo is cross-submitted to three HackerNoon contests + DevNetwork.
See [HACKATHON.md](./HACKATHON.md).

- **HackerNoon Intelligent Search & Retrieval** ($60K Algolia credits, Jun 5).
- **HackerNoon Foundational Tech & Builder Innovation** ($5K cash + $750, Jun 5).
- **HackerNoon Graph-Powered Intelligence (Neo4j)** ($10K credits, Jun 5) —
  if paired with a downstream KG layer.
- **DevNetwork AI+ML 2026** — cross-submission.

## License

Apache 2.0. Mukunda Katta, independent developer.
