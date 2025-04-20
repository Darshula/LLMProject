from io import StringIO
import os
import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import re
import uuid
from dotenv import load_dotenv

from text2sql import text2sql
load_dotenv()

# ✅ DIRECTLY SET YOUR API KEY HERE
openai.api_key = os.getenv("OPENAI_KEY")

# Streamlit UI setup
st.title("News Researcher")
st.sidebar.title("Enter URLs")

# Function to fetch and extract text from URLs
def fetch_text_from_url(url):
    text: str = ''
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        main = soup.find('main')
        for p_tag in main.find_all('p'):
            text += p_tag.text + '\n'
        st.status(f'Extracted text:\n\n{text}')
        return text
    except requests.RequestException as e:
        st.error(f"Failed to retrieve data from {url}: {str(e)}")
    return ""

# Clean the extracted text
def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', ' ', text)

# Sidebar: URL Inputs
urls = [st.sidebar.text_input(f"URL {i+1}") for i in range(3)]
process_url_clicked = st.sidebar.button("Process URLs")

database_bin = st.sidebar.file_uploader("Upload a database")

database_file = {}
if database_bin is not None:
    db_location = os.path.dirname(os.path.realpath(__file__)) + '/uploads/db/' + str(uuid.uuid1()) + database_bin.name
    with open(db_location, 'wb') as database_file:
        database_file.write(database_bin.getvalue())
    text2sql(db_location)

# Store extracted texts
all_texts = []

def process_urls(urls):
    global all_texts
    all_texts = []
    for url in urls:
        if url.strip():
            raw_text = fetch_text_from_url(url)
            cleaned_text = clean_text(raw_text)
            if cleaned_text:
                percent_body_to_use = int(0.2 * len(cleaned_text))
                cleaned_text = cleaned_text[int(percent_body_to_use*1.2):-percent_body_to_use]
                all_texts.append(cleaned_text)
    if not all_texts:
        st.error("No valid text extracted from URLs. Please check the URLs and try again.")
    else:
        st.success("Texts processed successfully.")

if process_url_clicked:
    process_urls(urls)

# Text input for user question
query = st.text_input("Ask a question about the news:")

# Generate answer using OpenAI
def generate_answer(query):
    if not query:
        st.warning("Please enter a question.")
        return

    if not all_texts:
        st.error("Please process some URLs first.")
        return

    context = " ".join(all_texts)
    prompt = f"""You are writing condensed summaries of news articles as a paragraph containing 20 lines with as much detail as possible. Now, you need to {query}. Use only the following information:

{context}

Respond as a single informative paragraph with relevant details, no fluff."""

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return None

# Display the generated answer
if query:
    answer = generate_answer(query)
    if answer:
        st.write(answer)
