import fitz
import os
import uuid

def process_pdf(uploaded_file):
    pdf_path = os.path.join("uploads", "pdf", f"{uuid.uuid4()}_{uploaded_file.name}")
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.read())
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()
