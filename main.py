import os
import uuid
import re
import requests
import textwrap
import time
from bs4 import BeautifulSoup
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from cassandra.cluster import Cluster
from text2sql import text2sql, run_nl_query
from pdf_parser import process_pdf

load_dotenv()

@st.cache_resource
def get_openai():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@st.cache_resource
def get_pinecone_index():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENVIRONMENT","us-west1-gcp"))
    idx = os.getenv("PINECONE_INDEX","sagefusion-index")
    env = os.getenv("PINECONE_ENVIRONMENT","us-west1-gcp")
    region, cloud = env.split("-",1)
    if idx not in pc.list_indexes().names():
        pc.create_index(name=idx, dimension=1536, metric="cosine", spec=ServerlessSpec(cloud=cloud,region=region))
    return pc.Index(name=idx)

@st.cache_resource
def get_cassandra_session():
    cluster = Cluster([os.getenv("CASSANDRA_HOST","127.0.0.1")],port=int(os.getenv("CASSANDRA_PORT",9042)))
    sess = cluster.connect()
    ks = os.getenv("CASSANDRA_KEYSPACE","sagefusion")
    sess.execute(f"CREATE KEYSPACE IF NOT EXISTS {ks} WITH replication={{'class':'SimpleStrategy','replication_factor':'1'}}")
    sess.set_keyspace(ks)
    sess.execute("CREATE TABLE IF NOT EXISTS documents(doc_id text PRIMARY KEY, source text, content text)")
    return sess

client = get_openai()
index = get_pinecone_index()
session = get_cassandra_session()

if "seen_urls" not in st.session_state:
    st.session_state.seen_urls = set()

def chunk_text(text, chunk_size=200, overlap=50):
    tokens, chunks, i = text.split(), [], 0
    while i < len(tokens):
        end = min(i + chunk_size, len(tokens))
        chunks.append(" ".join(tokens[i:end]))
        if end == len(tokens):
            break
        i = end - overlap
    return chunks

def fetch_and_clean(url):
    r = requests.get(url, timeout=5)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.content, "html.parser")
    body = soup.body or soup
    text = body.get_text(separator=" ")
    return re.sub(r"[^\x00-\x7F]+"," ", text).strip()

def get_embedding(text):
    resp = client.embeddings.create(model="text-embedding-ada-002", input=[text])
    return resp.data[0].embedding

def ingest_chunks(chunks, source):
    upserts = []
    for chunk in chunks:
        doc_id = str(uuid.uuid4())
        emb = get_embedding(chunk)
        upserts.append((doc_id, emb, {"source":source}))
        session.execute("INSERT INTO documents(doc_id, source, content) VALUES (%s,%s,%s)",(doc_id,source,chunk))
    index.upsert(vectors=upserts)

def rag_retrieve_details(query, top_k=3):
    q_emb = get_embedding(query)
    resp = index.query(vector=q_emb, top_k=top_k, include_metadata=True)
    matches = sorted(resp.matches, key=lambda m: m.score, reverse=True)
    results = []
    for m in matches:
        row = session.execute("SELECT content FROM documents WHERE doc_id=%s",(m.id,)).one()
        if row:
            results.append({"score":m.score,"text":row.content})
    return results

def precision_at_k(retrieved, relevant, k=3):
    return len(set(retrieved[:k]) & set(relevant)) / k

def recall_at_k(retrieved, relevant, k=3):
    return len(set(retrieved[:k]) & set(relevant)) / len(relevant) if relevant else 0.0

def mrr(retrieved, relevant):
    for i,doc in enumerate(retrieved, start=1):
        if doc in relevant:
            return 1/i
    return 0.0

def faithfulness(answer, references):
    ans_tokens = set(answer.split())
    ref_tokens = set().union(*[set(r.split()) for r in references])
    return len(ans_tokens & ref_tokens)/len(ans_tokens) if ans_tokens else 0.0

st.title("FusionSage")

st.sidebar.header("Enter webpage URLs")
urls = [st.sidebar.text_input(f"URL {i+1}") for i in range(3)]

st.sidebar.header("Upload SQL schema (.sql)")
db_file = st.sidebar.file_uploader("", type="sql")
if db_file:
    path = os.path.join("uploads","db",f"{uuid.uuid4()}_{db_file.name}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,"wb") as f:
        f.write(db_file.getvalue())
    text2sql(path)

st.sidebar.header("Upload PDF")
pdf_file = st.sidebar.file_uploader("", type="pdf")
if pdf_file and "pdf_file" not in st.session_state:
    pdf_text = process_pdf(pdf_file)
    ingest_chunks(chunk_text(pdf_text),"pdf")
    st.session_state.pdf_file = pdf_file

mode = st.sidebar.selectbox("Select query mode",("Documents (Web/PDF)","Database"))
query = st.text_input("Enter your question:")

if st.button("Process"):
    for u in urls:
        if u.strip() and u not in st.session_state.seen_urls:
            txt = fetch_and_clean(u)
            if txt:
                ingest_chunks(chunk_text(txt),"webpage")
            st.session_state.seen_urls.add(u)
    if mode=="Database":
        if st.session_state.get("db_ready") and query:
            start_sql = time.time()
            output = run_nl_query(query)
            sql_time = time.time()-start_sql
            if "error" in output:
                st.error(output["error"])
            else:
                sql = output["query"]
                result = output["result"]
                st.code(sql,language="sql")
                st.markdown(f"- **SQL gen+exec time:** {sql_time:.2f}s")
                row_count = len(result)
                st.markdown(f"- **Rows returned:** {row_count}")
                if row_count==1 and len(result[0])==1:
                    cnt = result[0][0]
                    m = re.search(r'COUNT\(\"?(\w+)\"?\)',sql,re.IGNORECASE)
                    noun = m.group(1).lower().rstrip('id').rstrip('s') if m else "items"
                    st.write(f"There are {cnt} {noun}s.")
                else:
                    summary_prompt = f"SQL:\n{sql}\nResult:\n{result}\nQuestion: {query}\nSummarize the answer:"
                    start_ans = time.time()
                    resp = client.chat.completions.create(model="gpt-3.5-turbo",messages=[{"role":"system","content":"You are a helpful assistant."},{"role":"user","content":summary_prompt}],temperature=0.5,max_tokens=200)
                    ans_time = time.time()-start_ans
                    st.markdown(f"- **Answer gen time:** {ans_time:.2f}s")
                    st.write(resp.choices[0].message.content)
        else:
            st.error("Please upload a .sql file and enter a question.")
    else:
        matches = rag_retrieve_details(query,top_k=3)
        retrieved = [m["text"] for m in matches]
        relevant = retrieved[:1]
        ctx = "\n\n".join(retrieved)
        prompt_text = f"Use ONLY the passages below:\n\n{ctx}\n\nQuestion: {query}\nAnswer:"
        resp = client.chat.completions.create(model="gpt-3.5-turbo",messages=[{"role":"system","content":"You are a helpful assistant."},{"role":"user","content":prompt_text}],temperature=0.7,max_tokens=500)
        answer = resp.choices[0].message.content
        reference = [relevant[0].split()]
        candidate = answer.split()
        bleu = sentence_bleu(reference,candidate,smoothing_function=SmoothingFunction().method4)
        answer_relevance = matches[0]["score"] if matches else 0.0
        faith = faithfulness(answer, [m["text"] for m in matches])
        st.subheader("Answer")
        st.write(answer)
        st.subheader("Evaluation Metrics")
        st.markdown(f"- **Retrieval (K=3):**\n  - Precision@3: {precision_at_k(retrieved,relevant,3):.4f}  \n  - Recall@3:    {recall_at_k(retrieved,relevant,3):.4f}  \n  - MRR:         {mrr(retrieved,relevant):.4f}\n\n- **Answer Quality:**\n  - BLEU:               {bleu:.4f}  \n  - Answer Relevance:   {answer_relevance:.4f}  \n  - Faithfulness:       {faith:.4f}")
        st.subheader("Relevant Documents")
        for m in matches:
            with st.container():
                st.markdown(f"**Score: {m['score']:.4f}**")
                st.code(m["text"])
