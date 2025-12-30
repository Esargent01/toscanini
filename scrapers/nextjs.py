"""
Scraper for Next.js official documentation.
Targets: https://nextjs.org/docs/app/
"""

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from dataclasses import dataclass
from typing import List, Optional
import time


@dataclass
class DocPage:
    url: str
    title: str
    content: str  # Markdown content
    section: str  # e.g., "routing", "data-fetching"
    version: str  # e.g., "15"


# Key documentation pages to scrape
# Focus on App Router - this is what Lovable/Bolt generate
NEXTJS_DOC_URLS = [
    # Core concepts
    "https://nextjs.org/docs/app/building-your-application/routing",
    "https://nextjs.org/docs/app/building-your-application/routing/layouts-and-templates",
    "https://nextjs.org/docs/app/building-your-application/routing/pages",
    "https://nextjs.org/docs/app/building-your-application/routing/loading-ui-and-streaming",
    "https://nextjs.org/docs/app/building-your-application/routing/error-handling",
    "https://nextjs.org/docs/app/building-your-application/routing/middleware",

    # Data fetching
    "https://nextjs.org/docs/app/building-your-application/data-fetching/fetching",
    "https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations",

    # Rendering
    "https://nextjs.org/docs/app/building-your-application/rendering/server-components",
    "https://nextjs.org/docs/app/building-your-application/rendering/client-components",

    # Optimizing
    "https://nextjs.org/docs/app/building-your-application/optimizing/images",
    "https://nextjs.org/docs/app/building-your-application/optimizing/metadata",

    # API Reference - File Conventions
    "https://nextjs.org/docs/app/api-reference/file-conventions/page",
    "https://nextjs.org/docs/app/api-reference/file-conventions/layout",
    "https://nextjs.org/docs/app/api-reference/file-conventions/loading",
    "https://nextjs.org/docs/app/api-reference/file-conventions/error",
    "https://nextjs.org/docs/app/api-reference/file-conventions/route",
]


def scrape_nextjs_page(url: str) -> Optional[DocPage]:
    """Scrape a single Next.js documentation page."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Next.js docs use specific selectors for content
        # This may need adjustment if their site structure changes
        article = soup.find('article') or soup.find('main')

        if not article:
            print(f"Warning: No article found for {url}")
            return None

        # Get title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else url.split('/')[-1]

        # Convert to markdown, preserving code blocks
        content = md(str(article), heading_style="ATX", code_language_callback=lambda el: el.get('class', [''])[0].replace('language-', ''))

        # Extract section from URL
        # e.g., /docs/app/building-your-application/routing -> "routing"
        parts = url.split('/')
        section = parts[-2] if len(parts) > 1 else "general"

        return DocPage(
            url=url,
            title=title,
            content=content,
            section=section,
            version="15"  # Update as needed
        )

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def scrape_all_nextjs_docs() -> List[DocPage]:
    """Scrape all configured Next.js documentation pages."""
    docs = []

    for url in NEXTJS_DOC_URLS:
        print(f"Scraping: {url}")
        doc = scrape_nextjs_page(url)
        if doc:
            docs.append(doc)
        time.sleep(1)  # Be respectful to the server

    print(f"Scraped {len(docs)} Next.js documentation pages")
    return docs


if __name__ == "__main__":
    # Test the scraper
    docs = scrape_all_nextjs_docs()
    for doc in docs[:2]:
        print(f"\n--- {doc.title} ---")
        print(doc.content[:500])
