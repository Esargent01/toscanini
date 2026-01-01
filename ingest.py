"""
Main script to run the full ingestion pipeline.
Run this on a schedule (daily/weekly) to keep docs fresh.
"""

import argparse
from datetime import datetime
from typing import List

from scrapers.nextjs import scrape_all_nextjs_docs
from scrapers.owasp import scrape_all_owasp_docs
from scrapers.zod import scrape_all_zod_docs
from scrapers.accessibility import scrape_all_accessibility_docs
from processing.chunker import chunk_all_documents
from processing.embedder import DocumentEmbedder, prepare_for_storage
from database.vector_store import VectorStore


def run_ingestion(
    sources: List[str] = ["nextjs", "owasp", "zod", "accessibility"],
    clear_existing: bool = False
):
    """
    Run the full ingestion pipeline.

    Args:
        sources: Which documentation sources to ingest
        clear_existing: Whether to clear existing chunks before inserting
    """
    print(f"Starting ingestion at {datetime.now().isoformat()}")
    print(f"Sources: {sources}")

    # Initialize components
    embedder = DocumentEmbedder()
    store = VectorStore()

    all_docs = []

    # Scrape documentation
    if "nextjs" in sources:
        print("\n=== Scraping Next.js docs ===")
        nextjs_docs = scrape_all_nextjs_docs()
        all_docs.extend([
            {
                "content": doc.content,
                "url": doc.url,
                "type": "nextjs",
                "section": doc.section,
                "title": doc.title,
                "version": doc.version
            }
            for doc in nextjs_docs
        ])

    if "owasp" in sources:
        print("\n=== Scraping OWASP docs ===")
        owasp_docs = scrape_all_owasp_docs()
        all_docs.extend([
            {
                "content": doc.content,
                "url": doc.url,
                "type": "owasp",
                "section": doc.category,
                "title": doc.title,
                "version": ""
            }
            for doc in owasp_docs
        ])

    if "zod" in sources:
        print("\n=== Scraping Zod docs ===")
        zod_docs = scrape_all_zod_docs()
        all_docs.extend([
            {
                "content": doc.content,
                "url": doc.url,
                "type": "zod",
                "section": doc.section,
                "title": doc.title,
                "version": doc.version
            }
            for doc in zod_docs
        ])

    if "accessibility" in sources:
        print("\n=== Scraping Accessibility docs ===")
        a11y_docs = scrape_all_accessibility_docs()
        all_docs.extend([
            {
                "content": doc.content,
                "url": doc.url,
                "type": "accessibility",
                "section": doc.category,
                "title": doc.title,
                "version": doc.version
            }
            for doc in a11y_docs
        ])

    if not all_docs:
        print("No documents scraped. Exiting.")
        return

    # Chunk documents
    print(f"\n=== Chunking {len(all_docs)} documents ===")
    chunks = chunk_all_documents(all_docs)

    # Generate embeddings
    print(f"\n=== Generating embeddings ===")
    embeddings = embedder.embed_documents(chunks)

    # Prepare for storage
    records = prepare_for_storage(chunks, embeddings)

    # Clear existing if requested
    if clear_existing:
        print(f"\n=== Clearing existing chunks ===")
        for source in sources:
            store.clear_by_source_type(source)

    # Insert into vector store
    print(f"\n=== Inserting into vector store ===")
    store.insert_chunks(records)

    print(f"\n=== Ingestion complete at {datetime.now().isoformat()} ===")
    print(f"Total chunks indexed: {len(chunks)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAG ingestion pipeline")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["nextjs", "owasp", "zod", "accessibility"],
        help="Documentation sources to ingest (nextjs, owasp, zod, accessibility)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing chunks before inserting"
    )

    args = parser.parse_args()

    run_ingestion(
        sources=args.sources,
        clear_existing=args.clear
    )
