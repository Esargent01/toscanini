"""
Scraper for Zod documentation.
Targets: https://zod.dev/
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
    content: str
    section: str
    version: str


# Key Zod documentation pages
ZOD_DOC_URLS = [
    # Introduction and basics
    "https://zod.dev/?id=introduction",
    "https://zod.dev/?id=installation",
    "https://zod.dev/?id=basic-usage",

    # Primitives
    "https://zod.dev/?id=primitives",
    "https://zod.dev/?id=coercion-for-primitives",
    "https://zod.dev/?id=literals",

    # Complex types
    "https://zod.dev/?id=strings",
    "https://zod.dev/?id=numbers",
    "https://zod.dev/?id=bigints",
    "https://zod.dev/?id=booleans",
    "https://zod.dev/?id=dates",

    # Objects and arrays
    "https://zod.dev/?id=zod-objects",
    "https://zod.dev/?id=arrays",
    "https://zod.dev/?id=tuples",
    "https://zod.dev/?id=unions",
    "https://zod.dev/?id=discriminated-unions",
    "https://zod.dev/?id=records",
    "https://zod.dev/?id=maps",
    "https://zod.dev/?id=sets",

    # Advanced
    "https://zod.dev/?id=intersections",
    "https://zod.dev/?id=recursive-types",
    "https://zod.dev/?id=promises",
    "https://zod.dev/?id=instanceof",
    "https://zod.dev/?id=functions",
    "https://zod.dev/?id=preprocess",
    "https://zod.dev/?id=custom-schemas",

    # Schema methods
    "https://zod.dev/?id=schema-methods",
    "https://zod.dev/?id=parse",
    "https://zod.dev/?id=safeparse",
    "https://zod.dev/?id=refine",
    "https://zod.dev/?id=superrefine",
    "https://zod.dev/?id=transform",
    "https://zod.dev/?id=default",
    "https://zod.dev/?id=optional",
    "https://zod.dev/?id=nullable",

    # Error handling
    "https://zod.dev/?id=error-handling",
    "https://zod.dev/?id=error-formatting",
]


def scrape_zod_page(url: str) -> Optional[DocPage]:
    """Scrape the Zod documentation page."""
    try:
        # Zod uses a single-page app, so we scrape the main page
        base_url = "https://zod.dev/"
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Get the main content area
        content_area = soup.find('main') or soup.find('article') or soup.find('body')

        if not content_area:
            print(f"Warning: No content found for {url}")
            return None

        # Extract section ID from URL
        section_id = url.split('?id=')[-1] if '?id=' in url else "general"

        # Convert to markdown
        content = md(str(content_area), heading_style="ATX")

        return DocPage(
            url=url,
            title=f"Zod - {section_id.replace('-', ' ').title()}",
            content=content,
            section=section_id,
            version="3.x"
        )

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def scrape_all_zod_docs() -> List[DocPage]:
    """
    Scrape Zod documentation.

    Note: Zod uses a single-page documentation site, so we scrape
    the full page once and it contains all sections.
    """
    docs = []

    print("Scraping: https://zod.dev/")

    try:
        response = requests.get("https://zod.dev/", timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Get main content
        content_area = soup.find('main') or soup.find('article') or soup.find('body')

        if content_area:
            content = md(str(content_area), heading_style="ATX")

            # Create a single comprehensive doc
            docs.append(DocPage(
                url="https://zod.dev/",
                title="Zod Schema Validation",
                content=content,
                section="validation",
                version="3.x"
            ))

    except Exception as e:
        print(f"Error scraping Zod docs: {e}")

    print(f"Scraped {len(docs)} Zod documentation pages")
    return docs


if __name__ == "__main__":
    docs = scrape_all_zod_docs()
    for doc in docs:
        print(f"\n--- {doc.title} ---")
        print(doc.content[:500])
