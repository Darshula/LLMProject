# import streamlit as st
# import sqlite3
# from langchain_community.utilities import SQLDatabase


# def text2sql(db_location: str):
#     with st.status(f'Reading database at {db_location}') as status:
#         with open(f'{db_location}', 'r', encoding='utf8') as sql_file:
#             sql_script = sql_file.read()
#             db = sqlite3.connect(f'{db_location}.db')
#             cursor = db.cursor()
#             cursor.executescript(sql_script)
#             db.commit()
#             db.close()
#         status.update(label='Connecting to database')
#         db = SQLDatabase.from_uri(f'sqlite:///{db_location}.db')
#         status.update(label=f'''{db.dialect}
#         {db.get_usable_table_names()}
#         {db.run("SELECT * FROM Artist LIMIT 10;")}''')


# text2sql.py
import streamlit as st
import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
import os


def text2sql(db_location: str):
    try:
        st.info("Creating SQLite DB from uploaded .sql file...")

        with open(db_location, 'r', encoding='utf8') as sql_file:
            sql_script = sql_file.read()

        db_file_path = db_location + '.db'
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()

        st.success("✅ SQLite DB created successfully.")

        db_instance = SQLDatabase.from_uri(f"sqlite:///{db_file_path}")
        tables = db_instance.get_usable_table_names()

        if not tables:
            st.error("⚠️ No usable tables found in the database.")
            return

        st.success(f"✅ Tables found: {tables}")

        # Initialize the LangChain SQL Query Chain
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0,
                         api_key=os.getenv("OPENAI_API_KEY"))
        query_chain = create_sql_query_chain(llm, db_instance)

        # Save in session state
        st.session_state.db_chain = query_chain
        st.session_state.db_instance = db_instance
        st.session_state.db_ready = True

    except Exception as e:
        st.error(f"❌ Error during DB or chain setup: {str(e)}")


def run_nl_query(question: str):
    if not st.session_state.get("db_ready") or "db_chain" not in st.session_state:
        return {"error": "❌ No database loaded or chain not initialized."}

    try:
        # Step 1: Generate SQL
        generated_sql = st.session_state.db_chain.invoke(
            {"question": question})

        # Step 2: Run SQL
        db = st.session_state.db_instance
        result = db.run(generated_sql)

        return {
            "query": generated_sql,
            "result": result
        }

    except Exception as e:
        return {"error": f"Query failed: {e}"}
