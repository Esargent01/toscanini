"""
Generate embeddings using BGE model from Hugging Face.
"""

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from tqdm import tqdm

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import EMBEDDING_MODEL, EMBEDDING_DIMENSION
from processing.chunker import Chunk


class DocumentEmbedder:
    """
    Wrapper for BGE embedding model.

    BGE models work best with a query instruction prefix for retrieval tasks.
    For documents/passages, no instruction is needed.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # BGE-specific: instruction for query encoding
        # This improves retrieval accuracy
        self.query_instruction = "Represent this sentence for searching relevant passages: "

    def embed_documents(self, chunks: List[Chunk], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for document chunks.

        Documents don't need the query instruction prefix.
        """
        texts = [chunk.content for chunk in chunks]

        print(f"Embedding {len(texts)} chunks...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True  # For cosine similarity
        )

        return embeddings

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a search query.

        Uses the BGE query instruction prefix for better retrieval.
        """
        query_with_instruction = self.query_instruction + query

        embedding = self.model.encode(
            query_with_instruction,
            normalize_embeddings=True
        )

        return embedding

    def embed_queries(self, queries: List[str]) -> np.ndarray:
        """Batch embed multiple queries."""
        queries_with_instruction = [
            self.query_instruction + q for q in queries
        ]

        embeddings = self.model.encode(
            queries_with_instruction,
            normalize_embeddings=True
        )

        return embeddings


def prepare_for_storage(chunks: List[Chunk], embeddings: np.ndarray) -> List[dict]:
    """
    Prepare chunks and embeddings for database insertion.

    Returns list of dicts ready for Supabase insert.
    """
    records = []

    for chunk, embedding in zip(chunks, embeddings):
        record = {
            "content": chunk.content,
            "embedding": embedding.tolist(),  # pgvector expects list
            "source_url": chunk.metadata["source_url"],
            "source_type": chunk.metadata["source_type"],
            "section": chunk.metadata["section"],
            "title": chunk.metadata["title"],
            "version": chunk.metadata["version"],
            "token_count": chunk.token_count,
        }
        records.append(record)

    return records


if __name__ == "__main__":
    # Test embedding
    embedder = DocumentEmbedder()

    # Test document embedding
    test_chunks = [
        Chunk(
            content="Server Components allow you to write UI that can be rendered on the server.",
            metadata={"source_url": "test", "source_type": "nextjs", "section": "rendering", "title": "Test", "version": "15", "chunk_index": 0, "total_chunks": 1},
            token_count=15
        ),
        Chunk(
            content="Use bcrypt or Argon2 for password hashing. Never store plaintext passwords.",
            metadata={"source_url": "test", "source_type": "owasp", "section": "auth", "title": "Test", "version": "", "chunk_index": 0, "total_chunks": 1},
            token_count=14
        ),
    ]

    embeddings = embedder.embed_documents(test_chunks)
    print(f"Embedding shape: {embeddings.shape}")

    # Test query embedding
    query_embedding = embedder.embed_query("How do I hash passwords securely?")
    print(f"Query embedding shape: {query_embedding.shape}")

    # Test similarity
    similarities = embeddings @ query_embedding
    print(f"Similarities: {similarities}")
    # Expect: second chunk (about password hashing) should score higher
