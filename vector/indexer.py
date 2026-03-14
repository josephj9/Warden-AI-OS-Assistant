import uuid
import os

from .moorcheh import add_chunk
from tools.extract import extract_pdf, extract_text, chunk_text

from tools.files import scan_folder_recursive


def index_folder(folder):

    files = scan_folder_recursive(folder)

    for file in files:
        name = os.path.basename(file)
        chunk_id = str(uuid.uuid4())
        add_chunk(chunk_id, name, {"file_path": os.path.abspath(file)})