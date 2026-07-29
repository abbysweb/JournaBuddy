# Phase 1 Test Cases

## Verification Plan

### Test Case 1: Docker Containers Initialization
- **Action**: Run `docker-compose up -d --build` in the root directory.
- **Expected Result**: All containers (`api`, `postgres`, `minio`, `redis`, `worker-io`, `worker-llm`, `nginx`, `ollama-1`) start successfully without crashing.

### Test Case 2: MinIO Access
- **Action**: Navigate to `http://localhost:9001` in a web browser. Log in using `minioadmin` for both username and password.
- **Expected Result**: You can successfully log in and see the MinIO dashboard. The bucket `journabuddy-uploads` should be visible (or will be created automatically upon the first file upload).

### Test Case 3: API Health Check
- **Action**: Open a web browser or use `curl` to access `http://localhost/api/health` or `http://localhost:8000/health`.
- **Expected Result**: A JSON response returning `{"status": "ok"}`.

### Test Case 4: Basic PDF Upload
- **Action**: Use an API client (like Postman or curl) to send a POST request with a sample PDF to `http://localhost/api/upload` (or `http://localhost:8000/api/upload`).
  - `curl -X POST -F "file=@sample.pdf" http://localhost:8000/api/upload`
- **Expected Result**: 
  1. The API responds with a success message, a `task_id`, and `extracted_length`.
  2. The PDF is successfully saved in the `journabuddy-uploads` bucket in MinIO.

### Test Case 5: Frontend Scaffolding
- **Action**: Navigate to the `frontend` folder and run `npm run dev`. Access the provided localhost port in a browser.
- **Expected Result**: The default React/Vite welcome screen appears, confirming the UI framework is successfully scaffolded.
