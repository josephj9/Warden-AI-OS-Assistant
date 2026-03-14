import uuid
import os

from vector.chroma import add_chunk, collection
from tools.extract import extract_pdf, extract_text, chunk_text

from tools.files import scan_folder_recursive


def index_folder(folder):

    files = scan_folder_recursive(folder)

    ids = []
    docs = []
    metas = []

    for file in files:

        ids.append(os.path.abspath(file))
        docs.append(os.path.basename(file))
        metas.append({"file_path": os.path.abspath(file)})

    BATCH_SIZE = 100

    for i in range(0, len(ids), BATCH_SIZE):

        batch_ids = ids[i:i+BATCH_SIZE]
        batch_docs = docs[i:i+BATCH_SIZE]
        batch_meta = metas[i:i+BATCH_SIZE]

        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_meta
        )

        print(f"Indexed batch {i//BATCH_SIZE + 1}")