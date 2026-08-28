import streamlit as st, requests
URL = st.secrets["TURSO_URL"].rstrip("/") + "/v2/pipeline"
TOKEN = st.secrets["TURSO_TOKEN"]
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def q(sql):
    r = requests.post(URL, headers=H, json={"requests":[{"type":"execute","stmt":{"sql":sql}}]}).json()
    return r['results'][0]['response']['result']

tabelas = q("SELECT name FROM sqlite_master WHERE type='table'")['rows']
st.write("TABELAS QUE EXISTEM:")
for t in tabelas:
    nome = t[0]['value']
    st.write(f"-> {nome}")
    cols = q(f"PRAGMA table_info({nome})")['rows']
    st.write(cols)
    st.write("---")
