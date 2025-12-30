"""
Scraper for OWASP Cheat Sheet Series.
Targets: https://cheatsheetseries.owasp.org/
"""

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from dataclasses import dataclass
from typing import List, Optional
import time


@dataclass
class SecurityDoc:
    url: str
    title: str
    content: str
    category: str  # e.g., "authentication", "session", "input-validation"


# Key OWASP cheat sheets for web app security
OWASP_CHEAT_SHEETS = [
    ("https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html", "authentication"),
    ("https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html", "session"),
    ("https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html", "input-validation"),
    ("https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html", "sql-injection"),
    ("https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html", "xss"),
    ("https://cheatsheetseries.owasp.org/cheatsheets/CSRF_Prevention_Cheat_Sheet.html", "csrf"),
    ("https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html", "password-storage"),
    ("https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html", "secrets"),
    ("https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html", "api-security"),
    ("https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html", "authorization"),
]


def scrape_owasp_page(url: str, category: str) -> Optional[SecurityDoc]:
    """Scrape a single OWASP cheat sheet."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # OWASP cheat sheets have content in main article
        article = soup.find('article') or soup.find('div', class_='md-content')

        if not article:
            print(f"Warning: No article found for {url}")
            return None

        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else category.title()

        content = md(str(article), heading_style="ATX")

        return SecurityDoc(
            url=url,
            title=title,
            content=content,
            category=category
        )

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def scrape_all_owasp_docs() -> List[SecurityDoc]:
    """Scrape all configured OWASP cheat sheets."""
    docs = []

    for url, category in OWASP_CHEAT_SHEETS:
        print(f"Scraping: {url}")
        doc = scrape_owasp_page(url, category)
        if doc:
            docs.append(doc)
        time.sleep(1)

    print(f"Scraped {len(docs)} OWASP cheat sheets")
    return docs


if __name__ == "__main__":
    docs = scrape_all_owasp_docs()
    for doc in docs[:2]:
        print(f"\n--- {doc.title} ({doc.category}) ---")
        print(doc.content[:500])
