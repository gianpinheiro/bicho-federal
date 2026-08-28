import streamlit as st, requests
URL = st.secrets["TURSO_URL"].rstrip("/") + "/v2/pipeline"
TOKEN = st.secrets["TURSO_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def consulta(sql):
    payload = {"requests": [{"type":"execute","stmt":{"sql": sql}}]}
    r = requests.post(URL, headers=HEADERS, json=payload).json()
    st.code(sql)
    st.json(r)

consulta("SELECT * FROM banca_sorteios LIMIT 3")
consulta("SELECT * FROM bicho LIMIT 5")
