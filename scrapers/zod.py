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


# Zod documentation pages
ZOD_DOC_URLS = [
    # Core documentation
    ("https://zod.dev/basics", "basics", "Basic Usage"),
    ("https://zod.dev/api", "api", "Defining Schemas"),
    ("https://zod.dev/error-customization", "errors", "Customizing Errors"),
    ("https://zod.dev/error-formatting", "errors", "Formatting Errors"),
    ("https://zod.dev/metadata", "advanced", "Metadata and Registries"),
    ("https://zod.dev/json-schema", "advanced", "JSON Schema"),
    ("https://zod.dev/codecs", "advanced", "Codecs"),
    ("https://zod.dev/library-authors", "advanced", "For Library Authors"),

    # Package docs
    ("https://zod.dev/packages/zod", "packages", "Zod Package"),
    ("https://zod.dev/packages/mini", "packages", "Zod Mini"),
]


def scrape_zod_page(url: str, section: str, title: str) -> Optional[DocPage]:
    """Scrape a single Zod documentation page."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find main content area - Zod uses article or main
        content_area = soup.find('article') or soup.find('main')

        if not content_area:
            # Try to find content div
            content_area = soup.find('div', class_='content') or soup.find('div', {'role': 'main'})

        if not content_area:
            print(f"Warning: No content found for {url}")
            return None

        # Remove navigation, sidebar, and footer elements
        for elem in content_area.find_all(['nav', 'aside', 'footer', 'header']):
            elem.decompose()

        # Remove any sponsor sections
        for elem in content_area.find_all(class_=lambda x: x and ('sponsor' in x.lower() or 'footer' in x.lower())):
            elem.decompose()

        # Get the actual title from the page if available
        title_elem = content_area.find('h1') or soup.find('h1')
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Convert to markdown
        content = md(str(content_area), heading_style="ATX")

        # Clean up excessive whitespace
        content = '\n'.join(line for line in content.split('\n') if line.strip())

        if len(content) < 100:
            print(f"Warning: Very little content for {url}")
            return None

        return DocPage(
            url=url,
            title=title,
            content=content,
            section=section,
            version="3.x"
        )

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def scrape_all_zod_docs() -> List[DocPage]:
    """Scrape all Zod documentation pages."""
    docs = []

    for url, section, title in ZOD_DOC_URLS:
        print(f"Scraping: {url}")
        doc = scrape_zod_page(url, section, title)
        if doc:
            docs.append(doc)
        time.sleep(1)  # Be respectful to the server

    print(f"Scraped {len(docs)} Zod documentation pages")
    return docs


if __name__ == "__main__":
    docs = scrape_all_zod_docs()
    for doc in docs:
        print(f"\n--- {doc.title} ({doc.section}) ---")
        print(f"Content length: {len(doc.content)} chars")
        print(doc.content[:500])
