import os
from moorcheh_sdk import MoorchehClient
from dotenv import load_dotenv

load_dotenv()

# Initialize client
client = MoorchehClient(api_key=os.getenv("MOORCHEH_API_KEY"))

NAMESPACE = "agent"


def add_chunk(chunk_id, text, metadata):

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


def query_chunks(query_text, n=5):

    results = client.similarity_search.query(
        namespaces=[NAMESPACE],
        query=query_text,
        top_k=n
    )

    return results