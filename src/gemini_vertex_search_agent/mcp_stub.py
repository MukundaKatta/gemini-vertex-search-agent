"""Stub Vertex AI Search (Discovery Engine) MCP server.

Mirrors the Google Cloud Discovery Engine surface used for enterprise
document search:
  - `list_data_stores` — enumerate the available data stores
  - `search`           — search a data store, returns ranked doc results
                         with id/title/snippet/uri/score
  - `get_document`     — fetch the full indexed text for a doc id
  - `summarize_search` — search + return a one-paragraph synthesis with
                         verbatim quotes

Returns canned realistic responses so judges can reproduce the demo
without a Google Cloud project + Discovery Engine data store. The real
Vertex AI Search swap is a one env-var change (GOOGLE_CLOUD_PROJECT +
DATA_STORE_ID) — the agent code is unchanged.

Run with: python -m gemini_vertex_search_agent.mcp_stub

Submission: HackerNoon Intelligent Search & Retrieval (Algolia track),
            HackerNoon Foundational Tech & Builder Innovation,
            HackerNoon Graph-Powered Intelligence (Neo4j track),
            DevNetwork AI+ML 2026 (cross-submission).
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Canned data stores + search results + document corpus
# ---------------------------------------------------------------------------


_DATA_STORES: list[dict[str, Any]] = [
    {
        "id":            "engineering-docs-prod",
        "doc_count":     1247,
        "last_indexed":  "2026-05-19T08:14:00Z",
    },
]


# Verbatim runbook text. Every step/command/path the agent quotes back to
# the user must come from here byte-for-byte.
_RUNBOOK_DB_ROTATE_V3 = (
    "# Runbook: Production Database Credential Rotation v3\n"
    "\n"
    "Owner: platform-infra@acme.example  |  Last reviewed: 2026-05-12\n"
    "\n"
    "## Preconditions\n"
    "- You have jumpbox-prod-1 SSH access.\n"
    "- All 4 read replicas are healthy in the last 30 minutes.\n"
    "- No active incident on the #incidents channel.\n"
    "\n"
    "## Steps\n"
    "1. SSH into jumpbox-prod-1.\n"
    "2. Run rotate-prod-db-creds.sh in jumpbox-prod-1.\n"
    "3. Wait 15 minutes for replication lag to settle across the 4 replicas.\n"
    "4. Confirm with health-check-db.sh which must return PASS for all 4 replicas.\n"
    "5. Update the Vault entry kv/prod/db/primary with the new password.\n"
    "6. Page the on-call DBA if any replica returns FAIL.\n"
    "\n"
    "## Rollback\n"
    "Re-run rotate-prod-db-creds.sh --rollback within 30 minutes of the\n"
    "rotation. Beyond 30 minutes, restore from the daily snapshot.\n"
)


_RUNBOOK_VAULT_UNSEAL = (
    "# Runbook: Vault Unseal After Restart\n"
    "\n"
    "Owner: platform-infra@acme.example  |  Last reviewed: 2026-04-30\n"
    "\n"
    "## Steps\n"
    "1. SSH into each of the 3 Vault nodes (vault-prod-1, vault-prod-2, vault-prod-3).\n"
    "2. On each node, run vault operator unseal and paste 3 of the 5 unseal keys.\n"
    "3. Confirm with vault status that Sealed=false on all three nodes.\n"
)


_RUNBOOK_BACKUP_RESTORE = (
    "# Runbook: Backup Restore (Daily Snapshot)\n"
    "\n"
    "Owner: platform-infra@acme.example  |  Last reviewed: 2026-05-04\n"
    "\n"
    "## Steps\n"
    "1. Identify the snapshot id from gs://eng-backups-bucket/daily/.\n"
    "2. Run restore-from-snapshot.sh --snapshot-id <ID> on jumpbox-prod-1.\n"
    "3. Wait for replication catch-up, then run health-check-db.sh.\n"
)


_DOCUMENTS: dict[str, dict[str, Any]] = {
    "doc-runbook-db-rotate-v3": {
        "id":            "doc-runbook-db-rotate-v3",
        "title":         "Runbook: Production Database Credential Rotation v3",
        "uri":           "gs://eng-docs-bucket/runbooks/db-rotate-v3.md",
        "content":       _RUNBOOK_DB_ROTATE_V3,
        "indexed_at":    "2026-05-12T18:02:00Z",
        "data_store_id": "engineering-docs-prod",
    },
    "doc-runbook-vault-unseal": {
        "id":            "doc-runbook-vault-unseal",
        "title":         "Runbook: Vault Unseal After Restart",
        "uri":           "gs://eng-docs-bucket/runbooks/vault-unseal.md",
        "content":       _RUNBOOK_VAULT_UNSEAL,
        "indexed_at":    "2026-04-30T09:11:00Z",
        "data_store_id": "engineering-docs-prod",
    },
    "doc-runbook-backup-restore": {
        "id":            "doc-runbook-backup-restore",
        "title":         "Runbook: Backup Restore (Daily Snapshot)",
        "uri":           "gs://eng-docs-bucket/runbooks/backup-restore.md",
        "content":       _RUNBOOK_BACKUP_RESTORE,
        "indexed_at":    "2026-05-04T07:48:00Z",
        "data_store_id": "engineering-docs-prod",
    },
}


# Canned Discovery Engine search results, keyed by (data_store_id, query).
# The top result for the demo query points to the rotation runbook doc.
_SEARCH_RESULTS: dict[tuple[str, str], list[dict[str, Any]]] = {
    ("engineering-docs-prod",
     "how do I rotate the production database credentials"): [
        {
            "id":      "doc-runbook-db-rotate-v3",
            "title":   "Runbook: Production Database Credential Rotation v3",
            "snippet": (
                "Run rotate-prod-db-creds.sh in jumpbox-prod-1. Wait 15 minutes "
                "for replication lag. Confirm with health-check-db.sh which must "
                "return PASS for all 4 replicas."
            ),
            "uri":     "gs://eng-docs-bucket/runbooks/db-rotate-v3.md",
            "score":   0.94,
        },
        {
            "id":      "doc-runbook-vault-unseal",
            "title":   "Runbook: Vault Unseal After Restart",
            "snippet": (
                "Run vault operator unseal and paste 3 of the 5 unseal keys on "
                "each of vault-prod-1, vault-prod-2, vault-prod-3."
            ),
            "uri":     "gs://eng-docs-bucket/runbooks/vault-unseal.md",
            "score":   0.61,
        },
        {
            "id":      "doc-runbook-backup-restore",
            "title":   "Runbook: Backup Restore (Daily Snapshot)",
            "snippet": (
                "Identify the snapshot id from gs://eng-backups-bucket/daily/. "
                "Run restore-from-snapshot.sh --snapshot-id <ID> on "
                "jumpbox-prod-1, then health-check-db.sh."
            ),
            "uri":     "gs://eng-docs-bucket/runbooks/backup-restore.md",
            "score":   0.52,
        },
    ],
}


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def list_data_stores_response() -> dict[str, Any]:
    """Mirrors discoveryengine.DataStoreServiceClient.list_data_stores."""
    return {
        "data_stores": [dict(ds) for ds in _DATA_STORES],
    }


def search_response(query: str, data_store_id: str = "engineering-docs-prod",
                    page_size: int = 5) -> dict[str, Any]:
    """Mirrors discoveryengine.SearchServiceClient.search.

    Returns a Discovery Engine-shaped result envelope with the top docs.
    """
    key = (data_store_id, query)
    results = _SEARCH_RESULTS.get(key)
    if results is None:
        # Soft fallback so the agent can still reason about an unknown query.
        results = [{
            "id":      "stub-no-match",
            "title":   f"(stub) no canned results for {query!r}",
            "snippet": (
                "Vertex AI Search stub: this query has no canned results. "
                "In production the real Discovery Engine SearchService would "
                "return ranked results from the indexed data store."
            ),
            "uri":     "",
            "score":   0.0,
        }]
    capped = results[:max(1, int(page_size))]
    return {
        "query":           query,
        "data_store_id":   data_store_id,
        "result_count":    len(capped),
        "total_size":      len(results),
        "results":         capped,
        "searched_at":     NOW.isoformat(),
    }


def get_document_response(doc_id: str) -> dict[str, Any]:
    """Mirrors discoveryengine.DocumentServiceClient.get_document.

    Returns the full indexed document text + metadata.
    """
    doc = _DOCUMENTS.get(doc_id)
    if doc is None:
        return {
            "error": f"unknown doc_id {doc_id!r}",
            "known": list(_DOCUMENTS.keys()),
        }
    return dict(doc)


def summarize_search_response(query: str,
                              data_store_id: str = "engineering-docs-prod") -> dict[str, Any]:
    """Convenience: run a search and return a one-paragraph synthesis with
    verbatim quotes pulled from the top result's snippet."""
    search = search_response(query, data_store_id=data_store_id, page_size=3)
    top = search["results"][0] if search["results"] else None
    if top is None or top["id"] == "stub-no-match":
        return {
            "query":         query,
            "data_store_id": data_store_id,
            "summary":       "No matching documents indexed for this query.",
            "citations":     [],
            "top_score":     0.0,
        }
    summary = (
        f'Top match (score {top["score"]:.2f}) is "{top["title"]}". '
        f'Verbatim snippet: "{top["snippet"]}" '
        f'Source: {top["uri"]}.'
    )
    citations = [
        {"id": r["id"], "title": r["title"], "uri": r["uri"], "score": r["score"]}
        for r in search["results"]
    ]
    return {
        "query":         query,
        "data_store_id": data_store_id,
        "summary":       summary,
        "citations":     citations,
        "top_score":     top["score"],
    }


# ---------------------------------------------------------------------------
# MCP server wiring
# ---------------------------------------------------------------------------


def _make_server() -> Server:
    server = Server("vertex-ai-search-stub")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(name="list_data_stores",
                 description=("List the Vertex AI Search (Discovery Engine) "
                              "data stores this project has indexed. Returns "
                              "id, doc_count, and last_indexed timestamp."),
                 inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="search",
                 description=("Search a Discovery Engine data store. Returns "
                              "ranked document results with id, title, snippet, "
                              "uri, and relevance score. Always call this "
                              "before answering a doc-Q&A question."),
                 inputSchema={"type": "object",
                              "properties": {
                                  "query":         {"type": "string"},
                                  "data_store_id": {"type": "string",
                                                    "default": "engineering-docs-prod"},
                                  "page_size":     {"type": "integer", "default": 5},
                              },
                              "required": ["query"]}),
            Tool(name="get_document",
                 description=("Fetch the full indexed text + metadata for a "
                              "specific document by id. Use this after `search` "
                              "to read the doc you want to cite verbatim."),
                 inputSchema={"type": "object",
                              "properties": {"doc_id": {"type": "string"}},
                              "required": ["doc_id"]}),
            Tool(name="summarize_search",
                 description=("Run a search and return a one-paragraph synthesis "
                              "with verbatim quotes from the top match. Use this "
                              "when you want a quick answer without pulling full "
                              "document bodies."),
                 inputSchema={"type": "object",
                              "properties": {
                                  "query":         {"type": "string"},
                                  "data_store_id": {"type": "string",
                                                    "default": "engineering-docs-prod"},
                              },
                              "required": ["query"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        a = arguments
        if name == "list_data_stores":
            payload = list_data_stores_response()
        elif name == "search":
            payload = search_response(
                a.get("query", ""),
                a.get("data_store_id", "engineering-docs-prod"),
                int(a.get("page_size") or 5),
            )
        elif name == "get_document":
            payload = get_document_response(a.get("doc_id", ""))
        elif name == "summarize_search":
            payload = summarize_search_response(
                a.get("query", ""),
                a.get("data_store_id", "engineering-docs-prod"),
            )
        else:
            payload = {"error": f"unknown tool {name!r}"}
        return [TextContent(type="text", text=json.dumps(payload, indent=2, default=str))]

    return server


async def _main() -> None:
    server = _make_server()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
