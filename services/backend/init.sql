-- Initialize Scribe database schema

CREATE TABLE IF NOT EXISTS papers (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    authors TEXT[],
    summary TEXT,
    published_date TIMESTAMP,
    pdf_url VARCHAR,
    status VARCHAR DEFAULT 'new',
    is_bookmarked BOOLEAN DEFAULT FALSE,
    tenant_id VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id VARCHAR REFERENCES papers(id),
    title VARCHAR,
    messages JSONB,
    tenant_id VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id VARCHAR REFERENCES papers(id),
    slug VARCHAR UNIQUE,
    title VARCHAR,
    content_markdown TEXT,
    language VARCHAR DEFAULT 'en',
    status VARCHAR DEFAULT 'draft',
    published_at TIMESTAMP,
    substack_embed_code TEXT,
    tenant_id VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_papers_tenant ON papers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_papers_bookmarked ON papers(is_bookmarked);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_tenant ON chat_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_paper ON chat_sessions(paper_id);
CREATE INDEX IF NOT EXISTS idx_posts_tenant ON posts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_slug ON posts(slug);
