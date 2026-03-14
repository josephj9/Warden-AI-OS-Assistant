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

    if ids:
        collection.add(ids=ids, documents=docs, metadatas=metas)