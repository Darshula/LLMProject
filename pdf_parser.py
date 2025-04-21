# pdf_parser.py
import fitz  # PyMuPDF
import streamlit as st
import os
import uuid


def process_pdf(uploaded_file):
    try:
        pdf_path = os.path.join(
            "uploads", "pdf", f"{uuid.uuid4()}_{uploaded_file.name}")
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())

        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()

        st.session_state.pdf_text = text.strip()
        st.session_state.pdf_ready = True
        st.success("✅ PDF uploaded and content extracted.")

    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
        st.session_state.pdf_ready = False
