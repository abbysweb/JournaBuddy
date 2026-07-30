# Phase 5 Verification Test Cases

This document contains the manual and automated test procedures to verify the production hardening and observability features implemented in Phase 5.

## Test Case 5.1: Redis Duplicate Caching (Content-Addressable)
**Objective**: Ensure identical PDF uploads are intercepted by Redis to save compute resources.
1. Start the API and Redis services: `docker-compose up -d api redis`
2. Upload a sample manuscript `test_paper.pdf` via `POST /api/upload`.
3. Note the returned `task_id` and the time it takes to process.
4. Upload the exact same `test_paper.pdf` again immediately.
5. **Expected Result**: The API returns instantly (< 100ms) with the **same** `task_id` and a message stating "PDF matched existing record".

## Test Case 5.2: SlowAPI Rate Limiting
**Objective**: Ensure the backend protects against spam by limiting `/api/upload` requests.
1. Run a `for` loop in bash or a Python script to hit `POST /api/upload` 10 times in less than a minute.
2. **Expected Result**: The first 5 requests should succeed (status 200). The 6th request and onwards should fail with HTTP 429 Too Many Requests.
3. Wait 1 minute.
4. Send another request. It should succeed.

## Test Case 5.3: Prometheus Metrics Scraping
**Objective**: Ensure FastAPI is actively exposing system metrics.
1. Start the API service.
2. In a browser or curl, navigate to `http://localhost:8000/metrics`.
3. **Expected Result**: The endpoint returns plain-text Prometheus metrics including `http_requests_total`, `http_request_duration_seconds`, and `python_gc_objects_collected_total`.

## Test Case 5.4: Grafana Integration
**Objective**: Ensure Grafana can read the Prometheus endpoint.
1. Open `http://localhost:3000` (Grafana).
2. Go to Connections -> Data Sources -> Add Prometheus.
3. Set the URL to `http://prometheus:9090`.
4. Click "Save & Test".
5. **Expected Result**: Grafana reports "Data source is working".

## Test Case 5.5: GitHub Actions CI/CD Pipeline
**Objective**: Ensure the automated testing pipeline works on push.
1. Check the "Actions" tab in the GitHub repository.
2. Click on the latest run for the "CI" workflow.
3. **Expected Result**: The `test-backend` and `lint-frontend` jobs both completed successfully with a green checkmark.
