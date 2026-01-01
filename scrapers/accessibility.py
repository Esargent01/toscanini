"""
Scraper for accessibility best practices documentation.
Sources: MDN Web Accessibility Guide, W3C WAI
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
    category: str
    version: str


# MDN Accessibility documentation URLs
MDN_A11Y_URLS = [
    # Core concepts
    "https://developer.mozilla.org/en-US/docs/Learn/Accessibility/What_is_accessibility",
    "https://developer.mozilla.org/en-US/docs/Learn/Accessibility/HTML",
    "https://developer.mozilla.org/en-US/docs/Learn/Accessibility/CSS_and_JavaScript",
    "https://developer.mozilla.org/en-US/docs/Learn/Accessibility/WAI-ARIA_basics",
    "https://developer.mozilla.org/en-US/docs/Learn/Accessibility/Multimedia",
    "https://developer.mozilla.org/en-US/docs/Learn/Accessibility/Mobile",

    # ARIA guides
    "https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Roles",
    "https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Attributes",
    "https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions",

    # Specific patterns
    "https://developer.mozilla.org/en-US/docs/Web/Accessibility/Keyboard-navigable_JavaScript_widgets",
    "https://developer.mozilla.org/en-US/docs/Web/Accessibility/Understanding_WCAG",
]

# W3C WAI Quick Reference key pages
W3C_A11Y_URLS = [
    "https://www.w3.org/WAI/WCAG21/quickref/?versions=2.1&currentsidebar=%23702",
]


def scrape_mdn_page(url: str) -> Optional[DocPage]:
    """Scrape an MDN accessibility documentation page."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # MDN uses article for main content
        article = soup.find('article') or soup.find('main')

        if not article:
            print(f"Warning: No article found for {url}")
            return None

        # Get title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else url.split('/')[-1]

        # Remove navigation, TOC, and other non-content elements
        for elem in article.find_all(['nav', 'aside', 'footer']):
            elem.decompose()

        # Convert to markdown
        content = md(str(article), heading_style="ATX")

        # Extract category from URL
        if '/ARIA/' in url:
            category = "aria"
        elif '/Learn/' in url:
            category = "fundamentals"
        else:
            category = "general"

        return DocPage(
            url=url,
            title=title,
            content=content,
            category=category,
            version="WCAG 2.1"
        )

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def scrape_all_accessibility_docs() -> List[DocPage]:
    """Scrape all accessibility documentation pages."""
    docs = []

    # Scrape MDN accessibility guides
    for url in MDN_A11Y_URLS:
        print(f"Scraping: {url}")
        doc = scrape_mdn_page(url)
        if doc:
            docs.append(doc)
        time.sleep(1)  # Be respectful to the server

    print(f"Scraped {len(docs)} accessibility documentation pages")
    return docs


if __name__ == "__main__":
    docs = scrape_all_accessibility_docs()
    for doc in docs[:2]:
        print(f"\n--- {doc.title} ---")
        print(doc.content[:500])
