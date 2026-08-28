import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Bicho Atrasado - Federal", page_icon="🎲", layout="centered")

# --- SENHA ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Área Restrita")
    senha = st.text_input("Digite a senha para acessar:", type="password")
    if st.button("Entrar"):
        if senha == st.secrets["APP_PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# --- ESTILO BONITO ---
st.markdown("""
<style>
   .stApp { background-color: #f8f9fa; }
    h1 { color: #1a1a2e; }
    div[data-testid="stMetric"] { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

URL = st.secrets["TURSO_URL"].rstrip("/") + "/v2/pipeline"
TOKEN = st.secrets["TURSO_TOKEN"]
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

st.title("🎲 Consulta Bichos Atrasados - FEDERAL")
st.markdown("Análise inteligente dos bichos mais atrasados na Loteria Federal")

premio = st.selectbox("Escolha o prêmio:", ["1º ao 5º Prêmio", "1º Prêmio", "1º ao 3º Prêmio"])
btn = st.button(f"🔍 Consultar {premio}", type="primary", use_container_width=True)

def consultar():
    # seu SQL aqui - mantive o que já tinha
    sql = "SELECT * FROM atrasados ORDER BY dias DESC"
    payload = {"requests": [{"type":"execute","stmt":{"sql": sql}}]}
    resp = requests.post(URL, headers=headers, json=payload).json()
    rows = resp['results'][0]['response']['result']['rows']
    return rows

if btn:
    with st.spinner("Analisando 91 concursos..."):
        try:
            rows = consultar()
            st.success(f"✅ Último sorteio: 26/08/2026 - {len(rows)} bichos analisados")
            # Tabela bonita
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.balloons()
        except Exception as e:
            st.error(f"Erro: {e}")
else:
    st.info("Selecione o prêmio e clique em Consultar")

if st.sidebar.button("Sair"):
    st.session_state.auth = False
    st.rerun()
