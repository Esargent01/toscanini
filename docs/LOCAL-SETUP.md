# Local Setup

## Prerequisites

- Python 3.9+
- Supabase account with pgvector enabled
- ~2GB disk space (for BGE embedding model)

## Installation

### 1. Clone and Install Dependencies

```bash
cd /path/to/toscanini
pip install -r requirements.txt
```

This installs:
- `sentence-transformers` - BGE embedding model
- `supabase` - Database client
- `fastapi` + `uvicorn` - API server
- `beautifulsoup4` + `markdownify` - Web scraping
- `langchain` - Text chunking

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

### 3. Set Up Supabase Database

Run these SQL commands in the Supabase SQL Editor:

**Enable pgvector and create table:**

```sql
-- Enable pgvector extension
create extension if not exists vector;

-- Create the table
create table doc_chunks (
    id bigserial primary key,
    content text not null,
    embedding vector(768),
    source_url text,
    source_type text,
    section text,
    title text,
    version text,
    token_count integer,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create index for fast similarity search
create index on doc_chunks
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Create index for filtering
create index on doc_chunks (source_type);
create index on doc_chunks (section);
```

**Create the search function:**

```sql
create or replace function match_doc_chunks(
    query_embedding vector(768),
    match_count int default 5,
    match_threshold float default 0.7,
    filter_source_types text[] default null,
    filter_sections text[] default null
)
returns table (
    id bigint,
    content text,
    source_url text,
    source_type text,
    section text,
    title text,
    version text,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        dc.id,
        dc.content,
        dc.source_url,
        dc.source_type,
        dc.section,
        dc.title,
        dc.version,
        1 - (dc.embedding <=> query_embedding) as similarity
    from doc_chunks dc
    where
        (filter_source_types is null or dc.source_type = any(filter_source_types))
        and (filter_sections is null or dc.section = any(filter_sections))
        and 1 - (dc.embedding <=> query_embedding) > match_threshold
    order by dc.embedding <=> query_embedding
    limit match_count;
end;
$$;
```

## Running the Ingestion Pipeline

The ingestion pipeline scrapes documentation, chunks it, generates embeddings, and stores them in Supabase.

### Full Ingestion

```bash
python ingest.py --sources nextjs owasp --clear
```

Options:
- `--sources`: Which doc sources to ingest (default: `nextjs owasp`)
- `--clear`: Clear existing chunks before inserting (recommended for updates)

### Partial Ingestion

To update only specific sources:

```bash
# Only Next.js docs
python ingest.py --sources nextjs --clear

# Only OWASP security docs
python ingest.py --sources owasp --clear
```

### What Gets Indexed

| Source | Documents | Chunks |
|--------|-----------|--------|
| Next.js | 17 pages (App Router docs) | ~144 chunks |
| OWASP | 9 cheat sheets (security) | ~225 chunks |
| **Total** | 26 documents | ~369 chunks |

## Running the API Server

### Development Mode

```bash
python -m uvicorn api.main:app --reload --port 8000
```

The `--reload` flag enables auto-reload on code changes.

### Production Mode

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Verify It's Working

```bash
# Health check
curl http://localhost:8000/health

# Test retrieval
curl -X POST http://localhost:8000/retrieve-for-context \
  -H "Content-Type: application/json" \
  -d '{"user_input": "SaaS app with user authentication"}'
```

## Configuration

Edit `config.py` to adjust:

```python
# Embedding model (768-dim vectors)
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

# Chunking parameters
CHUNK_SIZE = 512          # Tokens per chunk
CHUNK_OVERLAP = 50        # Overlap between chunks
MIN_CHUNK_SIZE = 100      # Skip chunks smaller than this

# Retrieval parameters
TOP_K = 5                 # Number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.3  # Minimum similarity score
```

## Troubleshooting

### "No results returned"

- Lower `SIMILARITY_THRESHOLD` in `config.py` (try 0.3 or 0.2)
- Verify data exists: check `doc_chunks` table in Supabase
- Check the query is meaningful (not empty)

### "Model loading slow"

First run downloads the BGE model (~400MB). Subsequent runs use the cached model.

### "Supabase connection failed"

- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`
- Ensure you're using the **service key** (not anon key) for write access
