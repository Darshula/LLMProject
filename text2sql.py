import streamlit as st
import sqlite3
from langchain_community.utilities import SQLDatabase


def text2sql(db_location: str):
    with st.status(f'Reading database at {db_location}') as status:
        with open(f'{db_location}', 'r', encoding='utf8') as sql_file:
            sql_script = sql_file.read()
            db = sqlite3.connect(f'{db_location}.db')
            cursor = db.cursor()
            cursor.executescript(sql_script)
            db.commit()
            db.close()
        status.update(label='Connecting to database')
        db = SQLDatabase.from_uri(f'sqlite:///{db_location}.db')
        status.update(label=f'''{db.dialect}
        {db.get_usable_table_names()}
        {db.run("SELECT * FROM Artist LIMIT 10;")}''')
