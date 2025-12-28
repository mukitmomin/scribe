-- Migration: Add tenant_id column for multi-tenancy support
-- Run this migration to prepare the database for multi-tenant mode

-- Add tenant_id column to papers table
ALTER TABLE papers ADD COLUMN IF NOT EXISTS tenant_id TEXT;

-- Add tenant_id column to chat_sessions table
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS tenant_id TEXT;

-- Add tenant_id column to posts table
ALTER TABLE posts ADD COLUMN IF NOT EXISTS tenant_id TEXT;

-- Create indexes for efficient tenant filtering
CREATE INDEX IF NOT EXISTS idx_papers_tenant ON papers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_tenant ON chat_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_posts_tenant ON posts(tenant_id);

-- Optional: Set default tenant for existing data
-- Uncomment these lines when ready to enable multi-tenancy
-- UPDATE papers SET tenant_id = 'default' WHERE tenant_id IS NULL;
-- UPDATE chat_sessions SET tenant_id = 'default' WHERE tenant_id IS NULL;
-- UPDATE posts SET tenant_id = 'default' WHERE tenant_id IS NULL;

-- Optional: Make tenant_id NOT NULL after migration
-- Uncomment these lines when ready to enforce multi-tenancy
-- ALTER TABLE papers ALTER COLUMN tenant_id SET NOT NULL;
-- ALTER TABLE chat_sessions ALTER COLUMN tenant_id SET NOT NULL;
-- ALTER TABLE posts ALTER COLUMN tenant_id SET NOT NULL;
