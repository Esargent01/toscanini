import os
from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for writes

# Embedding model
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIMENSION = 768  # BGE base outputs 768-dim vectors

# Chunking
CHUNK_SIZE = 512          # Tokens per chunk
CHUNK_OVERLAP = 50        # Overlap between chunks
MIN_CHUNK_SIZE = 100      # Skip chunks smaller than this

# Retrieval
TOP_K = 5                 # Number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.3  # Minimum similarity score (lowered for better recall)
