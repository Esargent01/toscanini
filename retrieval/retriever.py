"""
Retriever that integrates with Toscanini's generation pipeline.
"""

from typing import List, Optional
import numpy as np

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processing.embedder import DocumentEmbedder
from database.vector_store import VectorStore
from config import TOP_K


class ContextRetriever:
    """
    Retrieves relevant documentation chunks for context augmentation.
    """

    def __init__(self):
        self.embedder = DocumentEmbedder()
        self.store = VectorStore()

    def retrieve(
        self,
        query: str,
        source_types: Optional[List[str]] = None,
        top_k: int = TOP_K
    ) -> List[dict]:
        """
        Retrieve relevant documentation chunks for a query.

        Args:
            query: The search query (e.g., user's project description or specific question)
            source_types: Filter sources (e.g., ["nextjs"] for framework-specific)
            top_k: Number of chunks to retrieve

        Returns:
            List of relevant chunks with metadata
        """
        # Embed the query
        query_embedding = self.embedder.embed_query(query)

        # Search vector store
        results = self.store.search(
            query_embedding=query_embedding,
            source_types=source_types,
            top_k=top_k
        )

        return results

    def retrieve_for_context_generation(
        self,
        user_input: str,
        project_type: str = "web_app"
    ) -> dict:
        """
        Retrieve documentation relevant to a Toscanini generation request.

        This method formulates multiple queries to get comprehensive coverage:
        1. Framework patterns (Next.js)
        2. Security requirements
        3. SEO/performance (if user-facing)

        Args:
            user_input: The user's project description
            project_type: Type of project (affects which docs to prioritize)

        Returns:
            Dict with categorized documentation chunks
        """
        results = {
            "nextjs": [],
            "security": [],
            "seo": [],
        }

        # Query 1: Framework patterns based on user input
        nextjs_query = f"Next.js App Router implementation for: {user_input}"
        results["nextjs"] = self.retrieve(
            query=nextjs_query,
            source_types=["nextjs"],
            top_k=3
        )

        # Query 2: Security requirements
        # Formulate based on detected features in user input
        security_keywords = ["auth", "login", "user", "password", "payment", "stripe", "data"]
        needs_security = any(kw in user_input.lower() for kw in security_keywords)

        if needs_security:
            security_query = f"Security best practices for: {user_input}"
            results["security"] = self.retrieve(
                query=security_query,
                source_types=["owasp"],
                top_k=3
            )

        # Query 3: SEO (if it's a user-facing app)
        public_keywords = ["landing", "marketing", "blog", "portfolio", "business", "seo"]
        needs_seo = any(kw in user_input.lower() for kw in public_keywords)

        if needs_seo:
            seo_query = f"SEO and performance optimization for: {user_input}"
            results["seo"] = self.retrieve(
                query=seo_query,
                source_types=["seo"],
                top_k=2
            )

        return results

    def format_for_prompt(self, retrieved_docs: dict) -> str:
        """
        Format retrieved documentation for injection into the generation prompt.

        Returns a markdown-formatted string ready to insert into the prompt.
        """
        sections = []

        if retrieved_docs.get("nextjs"):
            nextjs_content = "\n\n".join([
                f"### {doc['title']}\n{doc['content']}"
                for doc in retrieved_docs["nextjs"]
            ])
            sections.append(f"## Next.js App Router Patterns\n\n{nextjs_content}")

        if retrieved_docs.get("security"):
            security_content = "\n\n".join([
                f"### {doc['title']}\n{doc['content']}"
                for doc in retrieved_docs["security"]
            ])
            sections.append(f"## Security Requirements (OWASP)\n\n{security_content}")

        if retrieved_docs.get("seo"):
            seo_content = "\n\n".join([
                f"### {doc['title']}\n{doc['content']}"
                for doc in retrieved_docs["seo"]
            ])
            sections.append(f"## SEO & Performance Guidelines\n\n{seo_content}")

        if not sections:
            return ""

        header = """## Reference Documentation

The following is current, authoritative documentation. Prioritize these patterns over general knowledge when they conflict.

"""
        return header + "\n\n---\n\n".join(sections)


# Example usage in your Toscanini pipeline
def augmented_context_generation(user_input: str, base_prompt: str) -> str:
    """
    Example of how to integrate RAG into your existing generation flow.
    """
    retriever = ContextRetriever()

    # Retrieve relevant docs
    retrieved = retriever.retrieve_for_context_generation(user_input)

    # Format for prompt
    doc_context = retriever.format_for_prompt(retrieved)

    # Combine with your base prompt
    augmented_prompt = f"""{base_prompt}

{doc_context}

## User Project Description

{user_input}

## Your Task

Generate a comprehensive context engineering file based on the reference documentation above.
"""

    return augmented_prompt


if __name__ == "__main__":
    # Test retrieval
    retriever = ContextRetriever()

    test_input = """
    I'm building a SaaS project management tool. Users need to sign up,
    create workspaces, invite team members, and manage tasks with due dates.
    I want Stripe for subscriptions and need it to be secure.
    """

    print("=== Retrieving documentation ===")
    docs = retriever.retrieve_for_context_generation(test_input)

    print(f"\nNext.js docs: {len(docs['nextjs'])} chunks")
    print(f"Security docs: {len(docs['security'])} chunks")
    print(f"SEO docs: {len(docs['seo'])} chunks")

    print("\n=== Formatted for prompt ===")
    formatted = retriever.format_for_prompt(docs)
    print(formatted[:1000])
