# # main.py
# import os
# import re
# import uuid
# import requests
# from bs4 import BeautifulSoup
# import openai
# import streamlit as st
# from dotenv import load_dotenv

# from text2sql import text2sql, run_nl_query

# load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")

# st.title("🧠 Smart Assistant: News or SQL")
# st.sidebar.header("🔗 Optional: Enter News URLs")
# urls = [st.sidebar.text_input(f"URL {i+1}") for i in range(3)]

# # Sidebar SQL uploader
# st.sidebar.header("📥 Optional: Upload SQL Schema File")
# db_file = st.sidebar.file_uploader("Upload .sql file", type=['sql'])
# if db_file:
#     db_dir = os.path.join(os.getcwd(), "uploads", "db")
#     os.makedirs(db_dir, exist_ok=True)
#     db_path = os.path.join(db_dir, str(uuid.uuid4()) + "_" + db_file.name)
#     with open(db_path, "wb") as f:
#         f.write(db_file.getvalue())
#     text2sql(db_path)

# # Common input field for a question
# query = st.text_input("💬 Enter a prompt:")

# # One common action button
# if st.button("🔍 Process"):
#     # CASE 1: URLs provided → summarize articles
#     if any(url.strip() for url in urls):
#         def fetch_text_from_url(url):
#             try:
#                 response = requests.get(url)
#                 response.encoding = 'utf-8'
#                 soup = BeautifulSoup(response.content, 'html.parser')
#                 main = soup.find('main') or soup
#                 return '\n'.join(p.text for p in main.find_all('p'))
#             except Exception as e:
#                 st.error(f"Error reading {url}: {e}")
#                 return ""

#         def clean_text(text):
#             return re.sub(r'[^\x00-\x7F]+', ' ', text)

#         all_texts = []
#         for url in urls:
#             if url.strip():
#                 raw = fetch_text_from_url(url)
#                 cleaned = clean_text(raw)
#                 chop = int(0.2 * len(cleaned))
#                 trimmed = cleaned[int(chop * 1.2):-chop]
#                 all_texts.append(trimmed)

#         if not all_texts:
#             st.error("❌ Could not extract valid text from URLs.")
#         elif not query:
#             st.warning("Please enter a prompt for summarization.")
#         else:
#             context = " ".join(all_texts)
#             prompt = f"""You are writing condensed summaries of news articles as a paragraph containing 20 lines with as much detail as possible. Now, you need to {query}. Use only the following information:

# {context}

# Respond as a single informative paragraph with relevant details, no fluff."""
#             try:
#                 response = openai.chat.completions.create(
#                     model="gpt-3.5-turbo",
#                     messages=[
#                         {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
#                         {"role": "user", "content": prompt}
#                     ],
#                     temperature=0.7,
#                     max_tokens=500
#                 )
#                 answer = response.choices[0].message.content
#                 st.subheader("📰 Answer:")
#                 st.write(answer)
#             except Exception as e:
#                 st.error(f"OpenAI API Error: {e}")

#     # CASE 2: No URLs → assume SQL question
#     elif st.session_state.get("db_ready") and query:
#         output = run_nl_query(query)
#         if "error" in output:
#             st.error(output["error"])
#         else:
#             st.code(output["query"], language="sql")
#             st.write("📊 Query Result:")
#             st.write(output["result"])

#     # CASE 3: No input
#     else:
#         st.warning(
#             "❗ Please enter a prompt and either URLs or upload a database.")


# main.py
import os
import re
import uuid
import requests
from bs4 import BeautifulSoup
import openai
import streamlit as st
from dotenv import load_dotenv

from text2sql import text2sql, run_nl_query
from pdf_parser import process_pdf

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("🧠 Smart Assistant: News, SQL, PDF")
st.sidebar.header("🔗 Optional: Enter News URLs")
urls = [st.sidebar.text_input(f"URL {i+1}") for i in range(3)]

# Upload SQL
st.sidebar.header("📥 Optional: Upload SQL Schema File")
db_file = st.sidebar.file_uploader("Upload .sql file", type=['sql'])
if db_file:
    db_dir = os.path.join(os.getcwd(), "uploads", "db")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, str(uuid.uuid4()) + "_" + db_file.name)
    with open(db_path, "wb") as f:
        f.write(db_file.getvalue())
    text2sql(db_path)

# Upload PDF
st.sidebar.header("📄 Optional: Upload a PDF File")
pdf_file = st.sidebar.file_uploader("Upload PDF", type=["pdf"])
if pdf_file:
    process_pdf(pdf_file)

# Common prompt input
query = st.text_input("💬 Enter a prompt/question:")

# Single action button
if st.button("🔍 Process"):
    # CASE 1: Process news
    if any(url.strip() for url in urls):
        def fetch_text_from_url(url):
            try:
                response = requests.get(url)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.content, 'html.parser')
                main = soup.find('main') or soup
                return '\n'.join(p.text for p in main.find_all('p'))
            except Exception as e:
                st.error(f"Error reading {url}: {e}")
                return ""

        def clean_text(text):
            return re.sub(r'[^\x00-\x7F]+', ' ', text)

        all_texts = []
        for url in urls:
            if url.strip():
                raw = fetch_text_from_url(url)
                cleaned = clean_text(raw)
                chop = int(0.2 * len(cleaned))
                trimmed = cleaned[int(chop * 1.2):-chop]
                all_texts.append(trimmed)

        if not all_texts:
            st.error("❌ Could not extract valid text from URLs.")
        elif not query:
            st.warning("Please enter a prompt for summarization.")
        else:
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
                answer = response.choices[0].message.content
                st.subheader("📰 News Answer:")
                st.write(answer)
            except Exception as e:
                st.error(f"OpenAI API Error: {e}")

    # CASE 2: SQL query
    elif st.session_state.get("db_ready") and query:
        output = run_nl_query(query)
        if "error" in output:
            st.error(output["error"])
        else:
            st.code(output["query"], language="sql")
            st.write("📊 Query Result:")
            st.write(output["result"])

    # CASE 3: PDF question
    elif st.session_state.get("pdf_ready") and query:
        context = st.session_state.pdf_text
        prompt = f"""You are reading a PDF document. Now, please answer this question using only the information from the document:

{context}

Question: {query}
Answer:"""

        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions from a PDF document."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            pdf_answer = response.choices[0].message.content
            st.subheader("📄 PDF Answer:")
            st.write(pdf_answer)
        except Exception as e:
            st.error(f"OpenAI PDF Error: {e}")

    else:
        st.warning(
            "❗ Please enter a prompt and either URLs, a database, or a PDF file.")
