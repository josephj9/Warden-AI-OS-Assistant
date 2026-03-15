import os
from moorcheh_sdk import MoorchehClient
from moorcheh_sdk.exceptions import APIError
from dotenv import load_dotenv

from .chroma import add_chunk as chroma_add_chunk, query_chunks as chroma_query_chunks

load_dotenv()

# Initialize client
client = MoorchehClient(api_key=os.getenv("MOORCHEH_API_KEY"))

NAMESPACE = "agent"


def add_chunk(chunk_id, text, metadata):
    """Try to store memory in Moorcheh; fallback to local Chroma on failure."""
    try:
        client.documents.upload(
            namespace_name=NAMESPACE,
            documents=[
                {
                    "id": chunk_id,
                    "text": text,
                    **metadata
                }
            ]
        )
    except APIError as e:
        print(f"Warning: Moorcheh API error, falling back to local Chroma: {e}")
        chroma_add_chunk(chunk_id, text, metadata)


def query_chunks(query_text, n=5):
    """Try Moorcheh semantic search; fallback to local Chroma on failure."""
    try:
        results = client.similarity_search.query(
            namespaces=[NAMESPACE],
            query=query_text,
            top_k=n
        )
        return results
    except APIError as e:
        print(f"Warning: Moorcheh query failed, falling back to local Chroma: {e}")
        return chroma_query_chunks(query_text, n)