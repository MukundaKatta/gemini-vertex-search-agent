from gemini_vertex_search_agent.mcp_stub import (
    _DATA_STORES,
    _DOCUMENTS,
    _SEARCH_RESULTS,
    get_document_response,
    list_data_stores_response,
    search_response,
    summarize_search_response,
)


def test_data_stores_seeded():
    assert len(_DATA_STORES) == 1
    ds = _DATA_STORES[0]
    assert ds["id"] == "engineering-docs-prod"
    assert ds["doc_count"] == 1247
    assert ds["last_indexed"] == "2026-05-19T08:14:00Z"


def test_documents_seeded():
    assert "doc-runbook-db-rotate-v3" in _DOCUMENTS
    assert "doc-runbook-vault-unseal" in _DOCUMENTS
    assert "doc-runbook-backup-restore" in _DOCUMENTS


def test_list_data_stores_returns_engineering_docs():
    payload = list_data_stores_response()
    assert len(payload["data_stores"]) == 1
    ds = payload["data_stores"][0]
    assert ds["id"] == "engineering-docs-prod"
    assert ds["doc_count"] == 1247
    assert ds["last_indexed"] == "2026-05-19T08:14:00Z"


def test_search_known_query_returns_three_results():
    payload = search_response(
        "how do I rotate the production database credentials"
    )
    assert payload["data_store_id"] == "engineering-docs-prod"
    assert payload["result_count"] == 3
    top = payload["results"][0]
    assert top["id"] == "doc-runbook-db-rotate-v3"
    assert top["title"] == "Runbook: Production Database Credential Rotation v3"
    assert top["uri"] == "gs://eng-docs-bucket/runbooks/db-rotate-v3.md"
    assert top["score"] == 0.94
    assert "rotate-prod-db-creds.sh" in top["snippet"]
    assert "15 minutes" in top["snippet"]
    assert "health-check-db.sh" in top["snippet"]
    assert "PASS" in top["snippet"]


def test_search_unknown_query_returns_stub_fallback():
    payload = search_response("totally unrelated thing")
    assert payload["result_count"] == 1
    assert payload["results"][0]["id"] == "stub-no-match"
    assert payload["results"][0]["score"] == 0.0


def test_search_page_size_caps_results():
    payload = search_response(
        "how do I rotate the production database credentials",
        page_size=1,
    )
    assert payload["result_count"] == 1
    assert payload["total_size"] == 3


def test_get_document_runbook_has_full_text():
    payload = get_document_response("doc-runbook-db-rotate-v3")
    assert payload["id"] == "doc-runbook-db-rotate-v3"
    assert payload["uri"] == "gs://eng-docs-bucket/runbooks/db-rotate-v3.md"
    content = payload["content"]
    # Every quote the agent emits MUST appear byte-for-byte in this content.
    assert "rotate-prod-db-creds.sh" in content
    assert "jumpbox-prod-1" in content
    assert "Wait 15 minutes for replication lag" in content
    assert "health-check-db.sh" in content
    assert "PASS for all 4 replicas" in content


def test_get_document_unknown_returns_error_with_known_list():
    payload = get_document_response("doc-does-not-exist")
    assert "error" in payload
    assert "doc-runbook-db-rotate-v3" in payload["known"]


def test_summarize_search_returns_verbatim_snippet_with_citations():
    payload = summarize_search_response(
        "how do I rotate the production database credentials"
    )
    assert payload["top_score"] == 0.94
    assert "rotate-prod-db-creds.sh" in payload["summary"]
    assert "15 minutes" in payload["summary"]
    assert "gs://eng-docs-bucket/runbooks/db-rotate-v3.md" in payload["summary"]
    assert len(payload["citations"]) == 3
    assert payload["citations"][0]["id"] == "doc-runbook-db-rotate-v3"


def test_summarize_search_unknown_query_returns_empty():
    payload = summarize_search_response("totally unrelated thing")
    assert payload["citations"] == []
    assert payload["top_score"] == 0.0


def test_search_chain_is_consistent():
    """The agent's killer move: search -> get_document -> verbatim cite.

    The chain stays consistent: the top search result's id, title, uri,
    and snippet all line up with get_document on that same id, and the
    snippet's claims appear byte-for-byte in the full document body.
    """
    query = "how do I rotate the production database credentials"
    search = search_response(query)
    top = search["results"][0]
    doc = get_document_response(top["id"])

    assert top["id"] == doc["id"] == "doc-runbook-db-rotate-v3"
    assert top["title"] == doc["title"]
    assert top["uri"] == doc["uri"]

    # The snippet's load-bearing phrases must appear verbatim in the doc body.
    for phrase in (
        "rotate-prod-db-creds.sh",
        "jumpbox-prod-1",
        "health-check-db.sh",
        "PASS for all 4 replicas",
    ):
        assert phrase in top["snippet"], f"missing in snippet: {phrase}"
        assert phrase in doc["content"], f"missing in doc body: {phrase}"

    # And the snippet's "15 minutes" wording lines up with the doc body's
    # fuller "Wait 15 minutes for replication lag" sentence.
    assert "15 minutes" in top["snippet"]
    assert "Wait 15 minutes for replication lag" in doc["content"]
