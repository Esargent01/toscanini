# Toscanini Documentation

Toscanini is a RAG (Retrieval-Augmented Generation) system that provides authoritative documentation context for Kleiber's context generation.

## Contents

- [Local Setup](./LOCAL-SETUP.md) - How to run Toscanini locally
- [GitHub Actions](./GITHUB-ACTIONS.md) - Automated ingestion via GitHub Actions
- [API Reference](./API-REFERENCE.md) - FastAPI endpoints

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      TOSCANINI RAG SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   INGESTION (runs weekly)              RETRIEVAL (per request)   │
│   ┌──────────────────────┐            ┌──────────────────────┐  │
│   │ 1. Scrape docs       │            │ 1. Embed query       │  │
│   │    - Next.js         │            │    (BGE model)       │  │
│   │    - OWASP           │            │                      │  │
│   │                      │            │ 2. Search pgvector   │  │
│   │ 2. Chunk text        │            │    (similarity)      │  │
│   │    (512 tokens)      │            │                      │  │
│   │                      │            │ 3. Return top-k      │  │
│   │ 3. Embed chunks      │            │    chunks            │  │
│   │    (BGE model)       │            └──────────────────────┘  │
│   │                      │                      │               │
│   │ 4. Store in          │                      ▼               │
│   │    Supabase          │◀────────── Supabase pgvector        │
│   └──────────────────────┘            (369 doc chunks)          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your Supabase credentials

# 3. Run ingestion (first time)
python ingest.py --sources nextjs owasp --clear

# 4. Start API server
python -m uvicorn api.main:app --port 8000

# 5. Test
curl http://localhost:8000/health
```
