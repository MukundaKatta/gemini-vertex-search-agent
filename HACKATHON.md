# gemini-vertex-search-agent — cross-submission notes

This repo is submitted to four contests in 2026-05/06. The build is one
deliverable; each contest gets a track-specific framing of the same
agent.

## Repo / live demo
- Code: https://github.com/MukundaKatta/gemini-vertex-search-agent
- Live demo (Cloud Run): https://gemini-vertex-search-agent-1029931682737.us-central1.run.app
- Demo video: see `.video-build/demo.mp4`
- License: Apache 2.0

## What it is, in one paragraph
An enterprise document Q&A agent on Google Cloud Agent Builder (ADK) +
Gemini 2.5, wired to Vertex AI Search (Discovery Engine). The user asks
a plain-English question; the agent walks `list_data_stores → search →
get_document` against the indexed corpus and answers in five labeled
sections (ANSWER / SOURCES / KEY QUOTES / CONFIDENCE / NEXT STEP). Every
command, path, and number is byte-for-byte from the indexed source.

## Burns GenAI App Builder credits as designed
The agent calls Vertex AI Search (Discovery Engine) through the
GenAI App Builder surface for every query — a search request plus an
optional get_document fetch per question — which is exactly the
credit-burn pattern the GenAI App Builder credits subsidize.

---

## Contest 1: HackerNoon Intelligent Search & Retrieval (Algolia)
**Prize:** $60K Algolia credits  ·  **Deadline:** 2026-06-05

**Framing.** A search-and-retrieval agent that turns a plain-English
question into a ranked document lookup, then answers with the verbatim
text of the top match. The retrieval substrate is Vertex AI Search
(Discovery Engine); the same agent design swaps cleanly onto Algolia
by replacing the four FunctionTools in `src/gemini_vertex_search_agent/agent.py`
with Algolia's `searchSingleIndex` + `getObject`.

**What's intelligent about it:** the agent doesn't just emit results;
it reads the top hit, quotes byte-for-byte, and flags low CONFIDENCE
when the top relevance score drops below 0.5. That's the difference
between a search box and a search agent.

## Contest 2: HackerNoon Foundational Tech & Builder Innovation
**Prize:** $5K cash + $750  ·  **Deadline:** 2026-06-05

**Framing.** A foundational pattern for enterprise doc Q&A: ADK +
Gemini 2.5 + a swappable retrieval MCP. The repo is the reference
implementation — stub MCP for reproducibility, real Discovery Engine
SDK for production, identical agent code for both. Innovation is in
the strict verbatim-citation contract: numbers and commands must be
byte-for-byte from the retrieved doc, KEY QUOTES are unedited, and
CONFIDENCE is bound to the retrieval score.

## Contest 3: HackerNoon Graph-Powered Intelligence (Neo4j)
**Prize:** $10K credits  ·  **Deadline:** 2026-06-05

**Framing.** The Discovery Engine substrate is one retrieval layer;
pairs naturally with a Neo4j knowledge graph layer for entity-aware
search (e.g. resolve `jumpbox-prod-1` to a Neo4j node, walk its edges
to related runbooks). The current build ships the document-retrieval
half; the Neo4j layer is a one-tool extension via FunctionTool wrapping
`neo4j.Driver.execute_query`.

## Contest 4: DevNetwork [AI+ML] 2026
**Cross-submission.** Same build, framed as an applied AI+ML agent
that uses Gemini 2.5 + retrieval-augmented generation against an
enterprise corpus.

---

## Rule compliance
| Common rules | How we meet it |
|---|---|
| Original work | Repo init 2026-05-20, scaffolded from sibling project pattern, agent + tools rewritten from scratch for Vertex AI Search |
| OSI license | Apache 2.0 at repo root |
| Runs on web | Streamlit dashboard, Cloud Run deployable |
| Reproducible demo | Stub MCP ships in repo; `pytest -q` passes with zero cloud setup; smoke script verifies the live agent's verbatim citation |

## Built with
python, gemini, gemini-2-5, vertex-ai, vertex-ai-search, discovery-engine,
google-cloud-agent-builder, agent-development-kit, mcp,
model-context-protocol, streamlit, google-cloud-run, apache-2,
genai-app-builder
