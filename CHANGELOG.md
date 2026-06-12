# Changelog

All notable changes to Scribe are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com), and this project adheres to
[Semantic Versioning](https://semver.org).

## [2.0.0] — 2026-06-12

### Changed
- Complete rewrite: Scribe is now a Claude Code plugin, not a web app.
  Papers in, understanding out, in your terminal.

### Added
- Commands: `/scribe:scan`, `/scribe:learn`, `/scribe:review`, `/scribe:draft`.
- scout / tutor / reviewer skills, each backed by stdlib-only Python 3.11 fetch
  scripts (no installs).
- File-based state under `~/.scribe/` (interests, digests, inbox, notes,
  drafts) — no server, no database.

### Removed
- v1 Next.js web app, FastAPI backend, and monorepo packages. Preserved at tag
  `v1.0.0` and branch `v1-archive`.

## [1.0.0]

- Final v1: Next.js web app + FastAPI backend with arXiv/HN trend discovery,
  AI chat teaching, and blog-draft generation.
