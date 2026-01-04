# Scribe - AI Research Assistant

An AI-powered research assistant for discovering academic papers, learning through AI chat, and generating blog post drafts.

## Features

- **Paper Discovery** - Search and browse arXiv papers with standard or agentic search
- **Trend Discovery** - Find trending AI papers from HackerNews discussions
- **AI Teacher** - Chat with an AI that explains papers in depth, with LaTeX math support
- **Draft Generator** - Automatically generate blog post drafts from your chat sessions
- **Publisher Dashboard** - Manage drafts, publish posts, and add Substack embeds
- **Public Blog API** - Serve published posts to external applications

## Architecture

Scribe is a monorepo with shared packages:

```
scribe/
├── packages/
│   ├── types/           # @scribe/types - Shared TypeScript types
│   └── ui/              # @scribe/ui - Shared React components
├── apps/
│   └── web/             # Next.js frontend
└── services/
    └── backend/         # FastAPI backend with LangGraph agents
```

## Tech Stack

### Frontend
- Next.js 15+ (App Router)
- TypeScript
- Vercel AI SDK for streaming chat
- react-markdown with KaTeX for math rendering

### Backend
- FastAPI (Python 3.11+)
- LangGraph for AI agents
- Google Gemini for LLM
- PostgreSQL with SQLAlchemy (async)
- arXiv API integration

## Getting Started

### Prerequisites

- Node.js 20+
- pnpm 9+
- Python 3.9+ (3.11+ recommended)
- Docker & Docker Compose
- Google API Key (for Gemini)

### Quick Start (Recommended)

The easiest way to start development is with the `dev.sh` script:

```bash
# Clone the repository
cd scribe

# Copy environment file and add your Google API key
cp .env.example .env
# Edit .env and add GOOGLE_API_KEY

# Start everything (database, backend, frontend)
./dev.sh
```

This will:
1. Set up Python virtual environment
2. Install all dependencies
3. Build shared packages
4. Start PostgreSQL (Docker)
5. Start backend (http://localhost:8000)
6. Start frontend (http://localhost:3000)

### Other Commands

```bash
./dev.sh stop      # Stop all services
./dev.sh docker    # Start with Docker Compose (all services in containers)
./dev.sh clean     # Remove venv, node_modules, logs
```

### Manual Development Setup

If you prefer to run things manually:

```bash
# Install Node dependencies
pnpm install

# Build shared packages
pnpm --filter @scribe/types build
pnpm --filter @scribe/ui build

# Start database
docker compose up -d db

# Start the backend
cd services/backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Start the frontend (in another terminal)
cd apps/web
pnpm dev
```

## Testing

### Running Integration Tests

The API sanity check tests verify all endpoints are working:

```bash
# Ensure database is running
docker compose up -d db

# Run integration tests
cd services/backend
source venv/bin/activate
pytest tests/integration/test_api_sanity.py -v
```

### Quick Sanity Check Script

Run a quick check without pytest:

```bash
cd services/backend
source venv/bin/activate
python -c "from tests.integration.test_api_sanity import run_quick_sanity_check; run_quick_sanity_check()"
```

### Running All Tests

```bash
cd services/backend
pytest tests/ -v
```

## API Documentation

### Interactive Docs

When the backend is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Testing with Bruno

1. Import from OpenAPI: Download `http://localhost:8000/openapi.json`
2. In Bruno: Import Collection → OpenAPI/Swagger
3. Set environment variable `baseUrl` to `http://localhost:8000`

## Environment Variables

### Root `.env`

```env
# Database (PostgreSQL via Docker)
DATABASE_URL=postgresql+asyncpg://scribe:scribe@localhost:5432/scribedb

# LLM
GOOGLE_API_KEY=your-google-api-key
USE_MOCK_LLM=true  # Set to false for real LLM

# Multi-tenancy (disabled by default)
MULTI_TENANT_ENABLED=false

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

## API Reference

### Trend Discovery (`/api/v1/trends/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/trends/discover` | GET | Discover trending papers from social signals |
| `/api/v1/trends/hackernews` | GET | Get papers trending on HackerNews |

Query parameters: `topic`, `time_window`, `max_results`

### Papers (`/api/v1/papers/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/papers/trending` | GET | Search papers from arXiv |
| `/api/v1/papers/bookmarks` | GET | List bookmarked papers |
| `/api/v1/papers/{id}/bookmark` | PUT | Toggle bookmark |
| `/api/v1/papers/discover` | GET | Agentic paper discovery |

### Chat (`/api/v1/chat/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat/sessions/{paper_id}` | GET | List chat sessions |
| `/api/v1/chat/session/{id}` | GET | Get session with messages |
| `/api/v1/chat` | POST | Chat with teacher (SSE) |

### Scribe (`/api/v1/scribe/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/scribe/draft` | POST | Generate blog draft |
| `/api/v1/scribe/admin/posts` | GET | List all posts (admin) |
| `/api/v1/scribe/post/{id}` | GET/PUT/DELETE | Manage posts |

### Public API (`/api/public/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/public/blog/posts` | GET | List published posts |
| `/api/public/blog/post/{slug}` | GET | Get post by slug |

## Multi-Tenancy

Scribe is prepared for multi-tenant deployment:

1. All models include `tenant_id` column
2. Middleware extracts tenant from request context
3. Enable with `MULTI_TENANT_ENABLED=true`

To enable:
1. Run the migration: `psql < migrations/001_add_tenant_id.sql`
2. Configure authentication (Auth0/Clerk)
3. Set `MULTI_TENANT_ENABLED=true`

## Deployment

### Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Manual Deployment

1. Deploy PostgreSQL
2. Deploy backend to Cloud Run / ECS
3. Deploy frontend to Vercel / Cloudflare Pages
4. Configure environment variables

## License

Copyright (c) 2025 Mukit Momin. All Rights Reserved.

This is proprietary software. Unauthorized copying, distribution, modification, or use is strictly prohibited without express written permission.
