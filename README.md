# JournaBuddy

**JournaBuddy** is a Research Paper Intelligence Platform designed to help authors prepare their manuscripts. It combines three analysis layers (symbolic rule-based checks, statistical NLP, and semantic embedding with a knowledge graph) to evaluate and improve research papers prior to submission.

## Features

JournaBuddy aims to answer four core questions for authors:

1. **Is my paper ready to submit?** - *Manuscript Readiness Checker*
2. **Which journals fit my paper?** - *Journal Discovery & Matching*
3. **Are those journals trustworthy?** - *Journal Trust Scorer*
4. **How does my paper compare to its field?** - *BI Dashboard & Benchmarking*

## Architecture (Serverless Vercel Edge)

The project has transitioned to a highly scalable, serverless microservices architecture designed to run on the Vercel free tier with zero operational overhead:
- **Framework**: Next.js 15 (App Router).
- **Frontend**: React, TailwindCSS v4, and Glassmorphism UI.
- **Backend**: Vercel Serverless Functions (`/api/*`).
- **Database & Storage**: Supabase (Managed PostgreSQL + pgvector + Blob Storage).
- **AI / NLP**: Groq API (Llama-3 for high-speed inference) and Hugging Face Inference API (for zero-cost embeddings).
- **Background Tasks**: Upstash / Inngest serverless event queues.

For complete details on the implementation roadmap, database schema, and project vision, refer to the [Plan/Plan.md](Plan/Plan.md) document.

## Running the Application Locally

Make sure you have Node.js installed. Navigate to the `frontend` Next.js directory to start the development server:

```bash
cd frontend
npm install
npm run dev
```
Then, open your browser to `http://localhost:3000`.

## Project Structure

- `frontend/` - The Next.js monolithic repository containing both React UI and Serverless API Routes.
- `frontend-old/` - The legacy Vite-based React frontend.
- `Plan/` - Complete implementation plan, detailed database schema, and technology stack.

## Privacy & Security

JournaBuddy is built with security and privacy by design. All file processing is done securely via Supabase, and the architecture emphasizes data provenance to provide an accountable AI experience.
