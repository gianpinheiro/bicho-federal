import streamlit as st
import requests
URL = st.secrets["TURSO_URL"].rstrip("/") + "/v2/pipeline"
TOKEN = st.secrets["TURSO_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

payload = {"requests": [{"type":"execute","stmt":{"sql": "SELECT name FROM sqlite_master WHERE type='table'"}}]}
r = requests.post(URL, headers=HEADERS, json=payload).json()
st.json(r)
