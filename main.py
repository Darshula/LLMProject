# from text2sql import text2sql
# import os
# import streamlit as st
# import requests
# from bs4 import BeautifulSoup
# import openai
# import re
# import uuid

# from dotenv import load_dotenv
# load_dotenv()


# openai.api_key = os.getenv("OPENAI_KEY")

# st.title("News Researcher")
# st.sidebar.title("Enter URLs")


# def fetch_text_from_url(url):
#     '''Function to fetch and extract text from URLs'''
#     text: str = ''
#     try:
#         response = requests.get(url)
#         response.encoding = 'utf-8'
#         soup = BeautifulSoup(response.content, 'html.parser')
#         main = soup.find('main')
#         for p_tag in main.find_all('p'):
#             text += p_tag.text + '\n'
#         st.status(f'Extracted text:\n\n{text}')
#         return text
#     except requests.RequestException as e:
#         st.error(f"Failed to retrieve data from {url}: {str(e)}")
#     return ""


# def clean_text(text):
#     '''Clean the extracted text'''
#     return re.sub(r'[^\x00-\x7F]+', ' ', text)


# urls = [st.sidebar.text_input(f"URL {i+1}") for i in range(3)]
# process_url_clicked = st.sidebar.button("Process URLs")

# database_bin = st.sidebar.file_uploader("Upload a database")

# database_file = {}
# if database_bin is not None:
#     db_location = os.path.dirname(os.path.realpath(
#         __file__)) + '/uploads/db/' + str(uuid.uuid1()) + database_bin.name
#     with open(db_location, 'wb') as database_file:
#         database_file.write(database_bin.getvalue())
#     text2sql(db_location)

# all_texts = []


# def process_urls(urls):
#     global all_texts
#     all_texts = []
#     for url in urls:
#         if url.strip():
#             raw_text = fetch_text_from_url(url)
#             cleaned_text = clean_text(raw_text)
#             if cleaned_text:
#                 percent_body_to_use = int(0.2 * len(cleaned_text))
#                 cleaned_text = cleaned_text[int(
#                     percent_body_to_use*1.2):-percent_body_to_use]
#                 all_texts.append(cleaned_text)
#     if not all_texts:
#         st.error("No text was found in given URLs.")
#     else:
#         st.success("Texts processed successfully.")


# if process_url_clicked:
#     process_urls(urls)

# query = st.text_input("Ask a question about the news:")


# def generate_answer(query):
#     if not query:
#         st.warning("Please enter a question.")
#         return

#     if not all_texts:
#         st.error("Please process some URLs first.")
#         return

#     context = " ".join(all_texts)
#     prompt = f"""You are writing condensed summaries of news articles as a paragraph containing 20 lines with as much detail as possible. Now, you need to {query}. Use only the following information:

# {context}

# Respond as a single informative paragraph with relevant details, no fluff."""

#     try:
#         response = openai.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#             max_tokens=500
#         )
#         return response.choices[0].message.content
#     except Exception as e:
#         st.error(f"OpenAI API Error: {str(e)}")
#         return None


# if query:
#     answer = generate_answer(query)
#     if answer:
#         st.write(answer)

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

# st.title("News Researcher & SQL Assistant")

# # ----------------- Section 1: News Processing -----------------
# st.sidebar.header("News URLs")
# urls = [st.sidebar.text_input(f"URL {i+1}") for i in range(3)]
# process_url_clicked = st.sidebar.button("Process URLs")


# def fetch_text_from_url(url):
#     text = ''
#     try:
#         response = requests.get(url)
#         response.encoding = 'utf-8'
#         soup = BeautifulSoup(response.content, 'html.parser')
#         main = soup.find('main') or soup
#         for p in main.find_all('p'):
#             text += p.text + '\n'
#         return text
#     except Exception as e:
#         st.error(f"Error reading {url}: {e}")
#         return ""


# def clean_text(text):
#     return re.sub(r'[^\x00-\x7F]+', ' ', text)


# all_texts = []


# def process_urls(urls):
#     global all_texts
#     all_texts = []
#     for url in urls:
#         if url.strip():
#             raw = fetch_text_from_url(url)
#             cleaned = clean_text(raw)
#             if cleaned:
#                 chop = int(0.2 * len(cleaned))
#                 cleaned = cleaned[int(chop * 1.2):-chop]
#                 all_texts.append(cleaned)
#     if all_texts:
#         st.success("✅ Text extracted from URLs.")
#     else:
#         st.error("❌ No valid content found in URLs.")


# if process_url_clicked:
#     process_urls(urls)

# query = st.text_input("Ask a question about the news articles:")


# def generate_answer(query):
#     if not all_texts:
#         st.warning("Please process URLs first.")
#         return
#     context = " ".join(all_texts)
#     prompt = f"""You are writing condensed summaries of news articles as a paragraph with 20 lines and as much detail as possible. Now, you need to {query}. Use only the following info:

# {context}

# Respond as a single informative paragraph with relevant details, no fluff."""

#     try:
#         response = openai.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#             max_tokens=500
#         )
#         return response.choices[0].message.content
#     except Exception as e:
#         st.error(f"OpenAI error: {e}")
#         return None


# if query:
#     result = generate_answer(query)
#     if result:
#         st.subheader("Answer:")
#         st.write(result)

# # ----------------- Section 2: SQL Upload and Query -----------------
# st.sidebar.header("Upload a SQL Schema File")

# db_file = st.sidebar.file_uploader("Upload .sql file", type=['sql'])
# if db_file:
#     db_dir = os.path.join(os.getcwd(), "uploads", "db")
#     os.makedirs(db_dir, exist_ok=True)
#     db_path = os.path.join(db_dir, str(uuid.uuid4()) + "_" + db_file.name)
#     with open(db_path, "wb") as f:
#         f.write(db_file.getvalue())
#     text2sql(db_path)

# st.subheader("Ask a natural language question to your database")
# if not st.session_state.get("db_ready"):
#     st.info("📥 Upload a .sql file to start.")
# else:
#     db_q = st.text_input("E.g., How many employees are there?")
#     if db_q:
#         output = run_nl_query(db_q)
#         if "error" in output:
#             st.error(output["error"])
#         else:
#             st.code(output["query"], language="sql")
#             st.write("Query Result:")
#             st.write(output["result"])

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

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("🧠 Smart Assistant: News or SQL")
st.sidebar.header("🔗 Optional: Enter News URLs")
urls = [st.sidebar.text_input(f"URL {i+1}") for i in range(3)]

# Sidebar SQL uploader
st.sidebar.header("📥 Optional: Upload SQL Schema File")
db_file = st.sidebar.file_uploader("Upload .sql file", type=['sql'])
if db_file:
    db_dir = os.path.join(os.getcwd(), "uploads", "db")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, str(uuid.uuid4()) + "_" + db_file.name)
    with open(db_path, "wb") as f:
        f.write(db_file.getvalue())
    text2sql(db_path)

# Common input field for a question
query = st.text_input("💬 Enter a prompt:")

# One common action button
if st.button("🔍 Process"):
    # CASE 1: URLs provided → summarize articles
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
                st.subheader("📰 Answer:")
                st.write(answer)
            except Exception as e:
                st.error(f"OpenAI API Error: {e}")

    # CASE 2: No URLs → assume SQL question
    elif st.session_state.get("db_ready") and query:
        output = run_nl_query(query)
        if "error" in output:
            st.error(output["error"])
        else:
            st.code(output["query"], language="sql")
            st.write("📊 Query Result:")
            st.write(output["result"])

    # CASE 3: No input
    else:
        st.warning(
            "❗ Please enter a prompt and either URLs or upload a database.")
