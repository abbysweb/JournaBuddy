# JournaBuddy

**JournaBuddy** is a Research Paper Intelligence Platform designed to help authors prepare their manuscripts. It combines three analysis layers (symbolic rule-based checks, statistical NLP, and semantic embedding with a knowledge graph) to evaluate and improve research papers prior to submission.

## Features

JournaBuddy aims to answer four core questions for authors:

1. **Is my paper ready to submit?** - *Manuscript Readiness Checker*
2. **Which journals fit my paper?** - *Journal Discovery & Matching*
3. **Are those journals trustworthy?** - *Journal Trust Scorer*
4. **How does my paper compare to its field?** - *BI Dashboard & Benchmarking*

## Architecture

The system uses a modern, hybrid intelligence stack:
- **Frontend**: HTML/JS/CSS with a Glass-morphism UI.
- **Backend**: FastAPI (currently transitioning from Flask) handling REST API endpoints.
- **Data & Embedding layer**: Statistical NLP (`textstat`, `spaCy`) and Semantic Layer (`sentence-transformers`).
- **Database**: Postgres with pgvector (via Supabase) to track tasks, registries, metrics, and compute embeddings.

For more details on the implementation roadmap, database schema, and project vision, refer to the [Plan.md](Plan.md) document.

## Running the Application

You can run the application either locally (using a Python virtual environment) or via Docker.

### Option 1: Running Locally (Windows)
Make sure you have Python installed, then simply run:
```bash
run_local.bat
```
This script will automatically create a virtual environment (`.venv`), install dependencies, start the backend, and open your browser to `http://localhost:5000`.

### Option 2: Running with Docker
If you have Docker Desktop installed and running, you can start the application using:
```bash
run.bat
```
This will build the Docker containers and start the service. It opens your browser to `http://localhost:5001`.

## Project Structure

- `frontend/` - Frontend HTML, JavaScript, and CSS files.
- `backend/` - Python backend logic, API endpoints, and processing modules.
- `Plan.md` - Complete implementation plan, detailed database schema, and technology stack.
- `docker-compose.yml` & `Dockerfile` - Container configuration for the platform.

## Privacy & Security

JournaBuddy is built with security and privacy by design. All file processing is done securely, and the architecture emphasizes data provenance to provide an accountable AI experience.
