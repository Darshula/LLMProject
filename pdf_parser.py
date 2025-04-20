import streamlit as st

def process_pdf(pdf_location: str):
    st.status(f'Reading PDF file at {pdf_location}')
