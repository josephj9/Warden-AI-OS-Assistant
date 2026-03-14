from pathlib import Path
import pdfplumber

def chunk_text(text, chunk_size = 500):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunk= text[i:i+chunk_size]
        chunks.append(chunk)
    
    return chunks

#read pdf and word and other files

def extract_text(file_path):

    path = Path(file_path)

    if path.suffix == ".txt":
        return path.read_text(errors="ignore")

    return ""

def extract_pdf(file_path):

    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text