from chromadb.utils import embedding_functions
from chromadb import Client
from dotenv import load_dotenv

load_dotenv()

client = Client()

# Use local embeddings (no API call)
local_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"  # lightweight, fast
)

# Delete old collection if exists
try:
    client.delete_collection("files")
except:
    pass

collection = client.create_collection(
    name="files",
    embedding_function=local_ef
)

def add_chunk(chunk_id, text, metadata):
    collection.add(
        ids=[chunk_id],
        documents=[text],
        metadatas=[metadata]
    )

def query_chunks(query_text, n=5):
    results = collection.query(
        query_texts=[query_text],
        n_results=n
    )
    return results