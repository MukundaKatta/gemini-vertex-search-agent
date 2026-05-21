"""Real Vertex AI smoke test for gemini-vertex-search-agent.

Runs a doc-Q&A question end-to-end through Gemini 2.5 Flash on the
Vertex AI Search (Discovery Engine) MCP stub and verifies the agent
walks list_data_stores -> search -> get_document -> verbatim cite,
emits all 5 labeled sections, and quotes the runbook's exact command
("rotate-prod-db-creds.sh"), the exact wait ("15 minutes"), and the
exact doc-id ("doc-runbook-db-rotate-v3").

Usage:
    GOOGLE_CLOUD_PROJECT=careersavvy-mukunda \\
    GOOGLE_GENAI_USE_VERTEXAI=true \\
    GOOGLE_CLOUD_LOCATION=us-central1 \\
    .venv/bin/python scripts/smoke.py
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "careersavvy-mukunda")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

from gemini_vertex_search_agent.runner import ask  # noqa: E402


QUESTION = (
    "how do I rotate the production database credentials. Walk the Vertex "
    "AI Search tools — list_data_stores, then search the engineering-docs-prod "
    "data store, then get_document on the top hit — and output the labeled "
    "sections from your system prompt with byte-for-byte verbatim quotes."
)


def main() -> int:
    print("== gemini-vertex-search-agent smoke ==")
    print(f"project={os.environ.get('GOOGLE_CLOUD_PROJECT')}")
    print(f"location={os.environ.get('GOOGLE_CLOUD_LOCATION')}")
    print(f"vertexai={os.environ.get('GOOGLE_GENAI_USE_VERTEXAI')}")
    print()
    print(f"> {QUESTION}")
    print()

    resp = ask(QUESTION, stub=True)
    print("--- FINAL TEXT ---")
    print(resp.final_text or "(no final text)")
    print("--- END FINAL TEXT ---")
    print(f"events: {len(resp.events)}")

    text = resp.final_text or ""
    upper = text.upper()
    checks = {
        "has ANSWER section":                  "ANSWER" in upper,
        "has SOURCES section":                 "SOURCES" in upper,
        "has KEY QUOTES section":              "KEY QUOTES" in upper,
        "has CONFIDENCE section":              "CONFIDENCE" in upper,
        "has NEXT STEP section":               "NEXT STEP" in upper,
        "quotes rotate-prod-db-creds.sh":      "rotate-prod-db-creds.sh" in text,
        "quotes 15 minutes verbatim":          "15 minutes" in text,
        "cites doc-runbook-db-rotate-v3":      "doc-runbook-db-rotate-v3" in text,
    }
    print()
    print("--- CHECKS ---")
    for label, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
