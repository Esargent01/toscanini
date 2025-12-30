# GitHub Actions Setup

Toscanini includes a GitHub Actions workflow for automated weekly ingestion to keep documentation fresh.

## Workflow Location

`.github/workflows/ingest.yml`

## What It Does

- Runs weekly on Sundays at 2am UTC
- Scrapes latest Next.js and OWASP documentation
- Generates embeddings and updates the Supabase vector store
- Can be triggered manually via workflow_dispatch

## Setup Instructions

### 1. Add Repository Secrets

Go to your repository's **Settings > Secrets and variables > Actions** and add:

| Secret Name | Value |
|-------------|-------|
| `SUPABASE_URL` | Your Supabase project URL (e.g., `https://xxx.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | Your Supabase service role key |

### 2. Enable GitHub Actions

If not already enabled, go to **Actions** tab and enable workflows for the repository.

### 3. Verify Workflow File

Ensure `.github/workflows/ingest.yml` exists with this content:

```yaml
name: Update Documentation Index

on:
  schedule:
    # Run weekly on Sundays at 2am UTC
    - cron: '0 2 * * 0'
  workflow_dispatch:  # Allow manual trigger

jobs:
  ingest:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run ingestion
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
        run: |
          python ingest.py --sources nextjs owasp --clear
```

## Manual Trigger

To run ingestion manually:

1. Go to **Actions** tab in your repository
2. Select **Update Documentation Index** workflow
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## Monitoring

### View Run History

Go to **Actions > Update Documentation Index** to see:
- Past runs and their status
- Execution time
- Logs for debugging

### Expected Output

A successful run shows:
```
Scraping: https://nextjs.org/docs/app/...
Scraped 17 Next.js documentation pages
Scraping: https://cheatsheetseries.owasp.org/...
Scraped 9 OWASP cheat sheets
Chunking 26 documents...
Total chunks: 369
Embedding 369 chunks...
Inserted 369/369 chunks
Ingestion complete
```

## Customizing the Schedule

Modify the cron expression in `ingest.yml`:

```yaml
schedule:
  # Every day at midnight UTC
  - cron: '0 0 * * *'

  # Every Monday at 3am UTC
  - cron: '0 3 * * 1'

  # First day of each month at 4am UTC
  - cron: '0 4 1 * *'
```

## Adding More Documentation Sources

To add a new documentation source:

1. Create a new scraper in `scrapers/` (e.g., `scrapers/react.py`)
2. Add the source to `ingest.py`
3. Update the workflow if needed

## Cost Considerations

| Resource | Free Tier | Notes |
|----------|-----------|-------|
| GitHub Actions | 2,000 min/month | Ingestion takes ~5 min |
| Supabase | 500MB database | ~369 chunks = <1MB |

The weekly schedule uses ~20 minutes/month of GitHub Actions, well within free tier.
