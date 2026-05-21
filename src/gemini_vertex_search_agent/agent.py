"""ADK Gemini agent wired to Vertex AI Search (Discovery Engine).

Two modes:
- `stub=True` (default): a local MCP stub server with a canned engineering
  document corpus. Lets reviewers reproduce the demo with zero cloud setup.
- `stub=False`: real Vertex AI Search via the google-cloud-discoveryengine
  Python SDK. User supplies GOOGLE_CLOUD_PROJECT, DATA_STORE_ID, and
  (optionally) DISCOVERY_ENGINE_LOCATION; the agent gets four FunctionTools
  that wrap the real Discovery Engine API calls.

The agent takes a plain-English question, searches the indexed docs,
and answers with byte-for-byte verbatim citations.
"""

from __future__ import annotations

import os
import sys
from typing import Any


try:
    from google.adk.agents import LlmAgent
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from google.adk.tools import FunctionTool
    from mcp import StdioServerParameters
    _ADK_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ADK_AVAILABLE = False


SYSTEM_PROMPT = """\
You are an enterprise document Q&A agent. The user asks a question in
plain English about indexed engineering docs (runbooks, design docs,
postmortems, etc.). You answer with byte-for-byte verbatim citations
pulled from a Vertex AI Search (Discovery Engine) data store.

Workflow (do every step, in order):

1. `list_data_stores` once to confirm which data store you can query.
2. `search` with the user's question against that data store. Read the
   top 1-3 results' titles, snippets, uris, and relevance scores.
3. For the top result (and any other result with score >= 0.7), call
   `get_document` to fetch the full indexed text. Read it carefully —
   every step/command/path you quote MUST be copied from this text.
4. (Optional) `summarize_search` when a one-paragraph synthesis is
   enough and you do not need the full doc body.

Output EXACTLY these labeled sections, in this order:

ANSWER:      one or two sentences answering the user's question, with
              every step, command, path, and number copied verbatim from
              a `get_document` or `search` result. No paraphrasing.
SOURCES:     bulleted list of the doc ids + titles + URIs you actually
              consulted (not the full search result list). Each bullet:
              `- doc-id - title - uri`.
KEY QUOTES:  2-4 verbatim quotes from the docs, each tagged with the
              source doc-id. Quotes must be byte-for-byte; do not edit
              whitespace, casing, or punctuation.
CONFIDENCE:  one of "high" / "medium" / "low" with a one-sentence reason
              tied to the top search result's relevance score. If the best
              result has score < 0.5, set CONFIDENCE to "low" and say so.
NEXT STEP:   one concrete follow-up search the user could run.

Strict rules:
- Commands, file paths, script names, numbers, and version strings MUST
  be byte-for-byte from `get_document` or `search` results.
- Do NOT invent doc ids or URIs. Only cite ids that came back from
  `list_data_stores` / `search` / `get_document`.
- KEY QUOTES must be byte-for-byte from the retrieved text — no
  paraphrasing inside KEY QUOTES.
- If `search` returns the stub `no canned results` fallback, set
  CONFIDENCE to "low" and explain.
"""


# ---------------------------------------------------------------------------
# Real Vertex AI Search (Discovery Engine) tool wiring
# ---------------------------------------------------------------------------


def _real_discovery_engine_tools() -> list[Any]:
    """Return four FunctionTool wrappers that call the real Discovery Engine.

    Reads GOOGLE_CLOUD_PROJECT, DATA_STORE_ID, and DISCOVERY_ENGINE_LOCATION
    (default "global") from the environment. The Discovery Engine SDK is
    imported lazily so the stub path stays light.
    """
    from google.cloud import discoveryengine_v1 as discoveryengine  # noqa: E402

    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.environ.get("DISCOVERY_ENGINE_LOCATION", "global")
    default_data_store = os.environ.get("DATA_STORE_ID", "")

    def _data_store_path(data_store_id: str) -> str:
        return (
            f"projects/{project}/locations/{location}"
            f"/collections/default_collection/dataStores/{data_store_id}"
        )

    def _serving_config(data_store_id: str) -> str:
        return f"{_data_store_path(data_store_id)}/servingConfigs/default_search"

    def list_data_stores() -> dict[str, Any]:
        """List Vertex AI Search data stores in this project + location."""
        client = discoveryengine.DataStoreServiceClient()
        parent = (
            f"projects/{project}/locations/{location}"
            "/collections/default_collection"
        )
        out = []
        for ds in client.list_data_stores(parent=parent):
            # discoveryengine.DataStore -> last path segment is the id
            ds_id = ds.name.rsplit("/", 1)[-1]
            out.append({
                "id":           ds_id,
                "display_name": ds.display_name,
                "industry":     str(ds.industry_vertical),
                "create_time":  ds.create_time.isoformat() if ds.create_time else None,
            })
        return {"data_stores": out}

    def search(query: str, data_store_id: str = "", page_size: int = 5) -> dict[str, Any]:
        """Search a Discovery Engine data store. Returns ranked results."""
        ds_id = data_store_id or default_data_store
        if not ds_id:
            return {"error": "DATA_STORE_ID env var or data_store_id arg required"}
        client = discoveryengine.SearchServiceClient()
        req = discoveryengine.SearchRequest(
            serving_config=_serving_config(ds_id),
            query=query,
            page_size=int(page_size),
        )
        results = []
        resp = client.search(request=req)
        for r in resp.results:
            doc = r.document
            derived = dict(doc.derived_struct_data) if doc.derived_struct_data else {}
            snippets = derived.get("snippets") or []
            snippet_text = snippets[0].get("snippet", "") if snippets else ""
            results.append({
                "id":      doc.id,
                "title":   derived.get("title", ""),
                "snippet": snippet_text,
                "uri":     derived.get("link", ""),
                "score":   float(getattr(r, "model_scores", {}).get("relevance", 0.0))
                            if hasattr(r, "model_scores") else 0.0,
            })
        return {
            "query":         query,
            "data_store_id": ds_id,
            "result_count":  len(results),
            "results":       results,
        }

    def get_document(doc_id: str, data_store_id: str = "") -> dict[str, Any]:
        """Fetch the full indexed document text + metadata for a doc id."""
        ds_id = data_store_id or default_data_store
        if not ds_id:
            return {"error": "DATA_STORE_ID env var or data_store_id arg required"}
        client = discoveryengine.DocumentServiceClient()
        name = f"{_data_store_path(ds_id)}/branches/default_branch/documents/{doc_id}"
        doc = client.get_document(name=name)
        struct = dict(doc.struct_data) if doc.struct_data else {}
        return {
            "id":            doc.id,
            "title":         struct.get("title", ""),
            "uri":           doc.content.uri if doc.content else "",
            "content":       struct.get("content", ""),
            "data_store_id": ds_id,
        }

    def summarize_search(query: str, data_store_id: str = "") -> dict[str, Any]:
        """Search + ask Discovery Engine for an LLM summary of the top results."""
        ds_id = data_store_id or default_data_store
        if not ds_id:
            return {"error": "DATA_STORE_ID env var or data_store_id arg required"}
        client = discoveryengine.SearchServiceClient()
        req = discoveryengine.SearchRequest(
            serving_config=_serving_config(ds_id),
            query=query,
            page_size=3,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=3,
                    include_citations=True,
                ),
            ),
        )
        resp = client.search(request=req)
        summary_text = ""
        try:
            summary_text = resp.summary.summary_text or ""
        except Exception:
            summary_text = ""
        citations: list[dict[str, Any]] = []
        for r in resp.results:
            doc = r.document
            derived = dict(doc.derived_struct_data) if doc.derived_struct_data else {}
            citations.append({
                "id":    doc.id,
                "title": derived.get("title", ""),
                "uri":   derived.get("link", ""),
            })
        return {
            "query":         query,
            "data_store_id": ds_id,
            "summary":       summary_text,
            "citations":     citations,
        }

    return [
        FunctionTool(func=list_data_stores),
        FunctionTool(func=search),
        FunctionTool(func=get_document),
        FunctionTool(func=summarize_search),
    ]


def _vertex_toolset(stub: bool = True) -> Any:
    """Build the agent's tool surface.

    stub=True spawns the local MCP stub via stdio. stub=False returns
    real Discovery Engine FunctionTools backed by google-cloud-discoveryengine.
    """
    if not _ADK_AVAILABLE:
        raise ImportError(
            "google-adk and mcp must be installed: pip install google-adk mcp"
        )
    if stub:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "gemini_vertex_search_agent.mcp_stub"],
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        return McpToolset(connection_params=StdioConnectionParams(server_params=params))
    return _real_discovery_engine_tools()


def build_agent(model: str = "gemini-2.5-flash", stub: bool = True) -> Any:
    if not _ADK_AVAILABLE:
        return None
    tools = _vertex_toolset(stub=stub)
    if not isinstance(tools, list):
        tools = [tools]
    return LlmAgent(
        model=model,
        name="gemini_vertex_search_agent",
        instruction=SYSTEM_PROMPT,
        tools=tools,
    )
