from pathlib import Path
import pdfplumber
import PyPDF2
import re
import docx

def chunk_text(text, chunk_size = 500):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunk= text[i:i+chunk_size]
        chunks.append(chunk)
    
    return chunks

#read pdf and word and other files

def extract_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file.
    """
    text = ""

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return f"Error extracting PDF: {e}"

    return text

def extract_docx(file_path: str) -> str:
    """
    Extracts text from a .docx file.
    """
    try:
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        return f"Error extracting DOCX: {e}"

def extract_text(file_path: str) -> str:
    """
    Extracts text from a plain text file, PDF file, or DOCX file.
    """
    path = Path(file_path)

    if path.suffix == ".txt":
        return path.read_text(errors="ignore")
    elif path.suffix in [".pdf", ".docx"]:
        extract_function = extract_pdf if path.suffix == ".pdf" else extract_docx
        return extract_function(file_path)

    return ""