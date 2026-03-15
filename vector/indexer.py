import uuid
import os

from .chroma import collection
from tools.extract import extract_pdf, extract_text, chunk_text
from tools.files import scan_folder_recursive


def index_folder(folder):

    files = scan_folder_recursive(folder)

    ids = []
    docs = []
    metas = []

    for file in files:
        ids.append(str(uuid.uuid4()))  # Unique ID for each file
        docs.append(os.path.basename(file))
        metas.append({"file_path": os.path.abspath(file)})

    BATCH_SIZE = 5000
    for i in range(0, len(ids), BATCH_SIZE):
        batch_ids = ids[i:i+BATCH_SIZE]
        batch_docs = docs[i:i+BATCH_SIZE]
        batch_metas = metas[i:i+BATCH_SIZE]
        
        print(f"Indexing batch {i//BATCH_SIZE + 1}")
        collection.add(ids=batch_ids, documents=batch_docs, metadatas=batch_metas)