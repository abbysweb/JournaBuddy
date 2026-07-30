# Phase 3 Verification & Testing Plan
**External Enrichment & Journal Matching**

This document outlines the test cases to verify the new Phase 3 integrations.

## 1. External API Clients

### Test 1: Crossref DOI Validation
- **Action**: Run `enrich_references_task` on a document with known DOIs.
- **Expected**: `CrossrefClient` successfully hits `https://api.crossref.org/works/{doi}` and returns the canonical title and publisher. Invalid DOIs should return `None`.

### Test 2: OpenAlex Citation Fetching
- **Action**: Run `enrich_references_task`.
- **Expected**: `OpenAlexClient` fetches the citation count (`cited_by_count`) and primary concepts for valid DOIs.

### Test 3: DOAJ Legitimacy Check
- **Action**: Run `match_journals_task`.
- **Expected**: Top recommended journals have `is_doaj_indexed` appropriately flagged, indicating high trust/open-access legitimacy.

## 2. Journal Matching (`pgvector`)

### Test 4: Seed Journals Script
- **Action**: Run `podman exec journabuddy_api_1 python scripts/seed_journals.py`.
- **Expected**: Connects to Postgres, embeds 5 scopes using `sentence-transformers`, and inserts them into the `journals` table.

### Test 5: Cosine Similarity Matching
- **Action**: Complete a document upload pipeline.
- **Expected**: `JournalMatcher` computes the average vector for the manuscript chunks, runs `<=>` (cosine distance) against the `journals` table, and returns the top matches sorted by `compatibility_percent`.

## 3. Resilience & Auditing

### Test 6: Rate Limiting
- **Action**: Ensure `enrich_references_task` processes a maximum of 10 DOIs per run and enforces a `0.5s` delay between requests.
- **Expected**: No HTTP 429 Too Many Requests from Crossref/OpenAlex.

### Test 7: Provenance Engine Audit Log
- **Action**: Check PostgreSQL `provenance_log` after upload.
- **Expected**: Contains new metrics `reference_enrichment` and `journal_matches` detailing the exact data sources (`crossref`, `openalex`, `journals`, `doaj`) and confidence levels.
