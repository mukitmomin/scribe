# Scribe - AI Research Assistant

An AI-powered research assistant for discovering academic papers, learning through AI chat, and generating blog post drafts.

## Features

- **Paper Discovery** - Search and browse arXiv papers with standard or agentic search
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

- Node.js 18+
- pnpm 9+
- Python 3.11+
- Docker & Docker Compose (optional)
- Google API Key (for Gemini)

### Quick Start with Docker

```bash
# Clone the repository
cd scribe

# Copy environment file
cp .env.example .env

# Add your Google API key to .env
# GOOGLE_API_KEY=your-key-here

# Start all services
docker-compose up
```

Open [http://localhost:3000](http://localhost:3000) to use Scribe.

### Development Setup

```bash
# Install dependencies
pnpm install

# Build shared packages
pnpm --filter @scribe/types build
pnpm --filter @scribe/ui build

# Start the backend
cd services/backend
pip install -e .
uvicorn app.main:app --reload

# Start the frontend (in another terminal)
cd apps/web
pnpm dev
```

## Environment Variables

### Backend (`services/backend/.env`)

```env
# Database
DATABASE_URL=postgresql+asyncpg://scribe:scribe@localhost:5432/scribedb

# LLM
GOOGLE_API_KEY=your-google-api-key
USE_MOCK_LLM=false

# Multi-tenancy (disabled by default)
MULTI_TENANT_ENABLED=false

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend (`apps/web/.env`)

```env
BACKEND_URL=http://localhost:8000
```

## API Reference

### Versioned API (`/api/v1/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/papers/trending` | GET | Search papers from arXiv |
| `/api/v1/papers/bookmarks` | GET | List bookmarked papers |
| `/api/v1/papers/{id}/bookmark` | PUT | Toggle bookmark |
| `/api/v1/papers/discover` | GET | Agentic paper discovery |
| `/api/v1/chat/sessions/{paper_id}` | GET | List chat sessions |
| `/api/v1/chat/session/{id}` | GET | Get session with messages |
| `/api/v1/chat` | POST | Chat with teacher (SSE) |
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

To enable multi-tenancy:
1. Run the migration: `psql < migrations/001_add_tenant_id.sql`
2. Configure authentication (Auth0/Clerk)
3. Set `MULTI_TENANT_ENABLED=true`

## Deployment

### Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Kubernetes

Helm charts coming soon.

### Manual Deployment

1. Deploy PostgreSQL
2. Deploy backend to Cloud Run / ECS
3. Deploy frontend to Vercel / Cloudflare Pages
4. Configure environment variables

## Integration with Portfolio

Scribe exposes a public API that your portfolio can consume:

```typescript
// In your portfolio's config
export const config = {
    scribeApiUrl: process.env.SCRIBE_API_URL || 'https://scribe-api.example.com',
};

// Fetch published posts
const posts = await fetch(`${config.scribeApiUrl}/api/public/blog/posts`);
```

## License

MIT

## Contributing

Contributions welcome! Please read the contributing guidelines first.
