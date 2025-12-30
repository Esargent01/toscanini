"""
Vector store using Supabase with pgvector extension.
"""

from supabase import create_client, Client
from typing import List, Optional
import numpy as np

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SUPABASE_URL, SUPABASE_KEY, EMBEDDING_DIMENSION, TOP_K, SIMILARITY_THRESHOLD


class VectorStore:
    """
    Supabase pgvector wrapper for document storage and retrieval.
    """

    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.table_name = "doc_chunks"

    def setup_table(self):
        """
        Create the table if it doesn't exist.

        Run this SQL in Supabase SQL Editor first:

        -- Enable pgvector extension
        create extension if not exists vector;

        -- Create the table
        create table doc_chunks (
            id bigserial primary key,
            content text not null,
            embedding vector(768),  -- BGE base dimension
            source_url text,
            source_type text,       -- 'nextjs', 'owasp', 'seo'
            section text,
            title text,
            version text,
            token_count integer,
            created_at timestamp with time zone default timezone('utc'::text, now())
        );

        -- Create index for fast similarity search
        create index on doc_chunks
        using ivfflat (embedding vector_cosine_ops)
        with (lists = 100);

        -- Create index for filtering
        create index on doc_chunks (source_type);
        create index on doc_chunks (section);
        """
        print("Table setup SQL provided in docstring. Run in Supabase SQL Editor.")

    def insert_chunks(self, records: List[dict], batch_size: int = 100):
        """
        Insert chunks with embeddings into the vector store.

        Args:
            records: List of dicts from prepare_for_storage()
            batch_size: Number of records per insert batch
        """
        total = len(records)
        inserted = 0

        for i in range(0, total, batch_size):
            batch = records[i:i + batch_size]

            # Supabase insert
            result = self.client.table(self.table_name).insert(batch).execute()

            inserted += len(batch)
            print(f"Inserted {inserted}/{total} chunks")

        print(f"Successfully inserted {total} chunks")

    def clear_by_source_type(self, source_type: str):
        """
        Delete all chunks of a specific source type.
        Useful for refreshing a single documentation source.
        """
        result = self.client.table(self.table_name)\
            .delete()\
            .eq("source_type", source_type)\
            .execute()

        print(f"Cleared chunks for source_type: {source_type}")

    def clear_all(self):
        """Delete all chunks. Use with caution!"""
        result = self.client.table(self.table_name)\
            .delete()\
            .neq("id", 0)\
            .execute()

        print("Cleared all chunks")

    def search(
        self,
        query_embedding: np.ndarray,
        source_types: Optional[List[str]] = None,
        sections: Optional[List[str]] = None,
        top_k: int = TOP_K,
        threshold: float = SIMILARITY_THRESHOLD
    ) -> List[dict]:
        """
        Search for similar chunks.

        Args:
            query_embedding: The query vector
            source_types: Filter by source type (e.g., ["nextjs", "owasp"])
            sections: Filter by section (e.g., ["authentication", "routing"])
            top_k: Number of results to return
            threshold: Minimum similarity score

        Returns:
            List of matching chunks with similarity scores
        """
        # Build the RPC call for vector similarity search
        # This requires a Supabase function (see setup below)

        params = {
            "query_embedding": query_embedding.tolist(),
            "match_count": top_k,
            "match_threshold": threshold,
        }

        if source_types:
            params["filter_source_types"] = source_types

        if sections:
            params["filter_sections"] = sections

        print(f"[VectorStore] Calling match_doc_chunks with params: match_count={params['match_count']}, threshold={params['match_threshold']}, source_types={params.get('filter_source_types')}")

        result = self.client.rpc("match_doc_chunks", params).execute()

        print(f"[VectorStore] Search returned {len(result.data) if result.data else 0} results")
        return result.data

    def get_search_function_sql(self) -> str:
        """
        Returns SQL to create the search function.
        Run this in Supabase SQL Editor.
        """
        return """
        create or replace function match_doc_chunks(
            query_embedding vector(768),
            match_count int default 5,
            match_threshold float default 0.7,
            filter_source_types text[] default null,
            filter_sections text[] default null
        )
        returns table (
            id bigint,
            content text,
            source_url text,
            source_type text,
            section text,
            title text,
            version text,
            similarity float
        )
        language plpgsql
        as $$
        begin
            return query
            select
                dc.id,
                dc.content,
                dc.source_url,
                dc.source_type,
                dc.section,
                dc.title,
                dc.version,
                1 - (dc.embedding <=> query_embedding) as similarity
            from doc_chunks dc
            where
                (filter_source_types is null or dc.source_type = any(filter_source_types))
                and (filter_sections is null or dc.section = any(filter_sections))
                and 1 - (dc.embedding <=> query_embedding) > match_threshold
            order by dc.embedding <=> query_embedding
            limit match_count;
        end;
        $$;
        """


if __name__ == "__main__":
    store = VectorStore()

    # Print setup SQL
    print("=== Table Setup SQL ===")
    store.setup_table()

    print("\n=== Search Function SQL ===")
    print(store.get_search_function_sql())
