"""
Smart chunking for technical documentation.
Preserves code blocks and semantic boundaries.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from dataclasses import dataclass
from typing import List
import re
import tiktoken

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE


@dataclass
class Chunk:
    content: str
    metadata: dict  # source, section, chunk_index, etc.
    token_count: int


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens using tiktoken (same tokenizer as Claude/GPT-4)."""
    encoder = tiktoken.get_encoding(model)
    return len(encoder.encode(text))


def create_splitter() -> RecursiveCharacterTextSplitter:
    """
    Create a text splitter optimized for technical documentation.

    Key decisions:
    - Split on markdown headers first (preserves sections)
    - Then paragraphs, then sentences
    - Keep code blocks together when possible
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE * 4,  # Approximate chars (4 chars ≈ 1 token)
        chunk_overlap=CHUNK_OVERLAP * 4,
        separators=[
            "\n## ",      # H2 headers (major sections)
            "\n### ",     # H3 headers (subsections)
            "\n#### ",    # H4 headers
            "\n```",      # Code block boundaries
            "\n\n",       # Paragraphs
            "\n",         # Lines
            ". ",         # Sentences
            " ",          # Words
            "",           # Characters (fallback)
        ],
        keep_separator=True,
        length_function=len,
    )


def preserve_code_blocks(text: str) -> List[str]:
    """
    Pre-process to identify and protect code blocks.
    Returns list of (content, is_code) tuples.
    """
    # Pattern matches fenced code blocks
    code_pattern = r'```[\s\S]*?```'

    parts = []
    last_end = 0

    for match in re.finditer(code_pattern, text):
        # Add text before code block
        if match.start() > last_end:
            parts.append(('text', text[last_end:match.start()]))
        # Add code block
        parts.append(('code', match.group()))
        last_end = match.end()

    # Add remaining text
    if last_end < len(text):
        parts.append(('text', text[last_end:]))

    return parts


def chunk_document(
    content: str,
    source_url: str,
    source_type: str,  # "nextjs", "owasp", "seo"
    section: str = "",
    title: str = "",
    version: str = ""
) -> List[Chunk]:
    """
    Chunk a document into retrieval-ready pieces.

    Args:
        content: The markdown content to chunk
        source_url: URL of the original document
        source_type: Category of documentation
        section: Sub-section within the doc type
        title: Document title
        version: Version info (e.g., "Next.js 15")

    Returns:
        List of Chunk objects ready for embedding
    """
    splitter = create_splitter()

    # Split the content
    raw_chunks = splitter.split_text(content)

    chunks = []
    for i, chunk_text in enumerate(raw_chunks):
        # Skip chunks that are too small (likely noise)
        token_count = count_tokens(chunk_text)
        if token_count < MIN_CHUNK_SIZE:
            continue

        # Build metadata for retrieval filtering
        metadata = {
            "source_url": source_url,
            "source_type": source_type,
            "section": section,
            "title": title,
            "version": version,
            "chunk_index": i,
            "total_chunks": len(raw_chunks),
        }

        chunks.append(Chunk(
            content=chunk_text.strip(),
            metadata=metadata,
            token_count=token_count
        ))

    return chunks


def chunk_all_documents(docs: List[dict]) -> List[Chunk]:
    """
    Process all scraped documents into chunks.

    Args:
        docs: List of dicts with keys: content, url, type, section, title, version

    Returns:
        List of all chunks ready for embedding
    """
    all_chunks = []

    for doc in docs:
        chunks = chunk_document(
            content=doc['content'],
            source_url=doc['url'],
            source_type=doc['type'],
            section=doc.get('section', ''),
            title=doc.get('title', ''),
            version=doc.get('version', '')
        )
        all_chunks.extend(chunks)
        print(f"  {doc['title']}: {len(chunks)} chunks")

    print(f"\nTotal chunks: {len(all_chunks)}")
    return all_chunks


if __name__ == "__main__":
    # Test chunking
    sample_doc = """
    # Server Components

    Server Components allow you to write UI that can be rendered on the server.

    ## Benefits

    ### Data Fetching

    Server Components allow you to move data fetching to the server, closer to your data source.

    ```tsx
    // This runs on the server
    async function Page() {
      const data = await fetch('https://api.example.com/data')
      return <div>{data}</div>
    }
    ```

    ### Security

    Server Components allow you to keep sensitive data and logic on the server, such as tokens and API keys.
    """

    chunks = chunk_document(
        content=sample_doc,
        source_url="https://nextjs.org/docs/app/building-your-application/rendering/server-components",
        source_type="nextjs",
        section="rendering",
        title="Server Components",
        version="15"
    )

    for chunk in chunks:
        print(f"\n--- Chunk {chunk.metadata['chunk_index']} ({chunk.token_count} tokens) ---")
        print(chunk.content[:200])
