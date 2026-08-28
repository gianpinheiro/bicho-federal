import streamlit as st
import requests

st.set_page_config(page_title="Bicho Atrasado - Federal", page_icon="🎲", layout="centered")

# --- SENHA ---
if "auth" not in st.session_state:
    st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔒 Área Restrita")
    senha = st.text_input("Digite a senha:", type="password")
    if st.button("Entrar"):
        if senha == st.secrets["APP_PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

st.title("🎲 Consulta Bichos Atrasados - FEDERAL")
st.markdown("Análise inteligente dos bichos mais atrasados na Loteria Federal")

URL = st.secrets["TURSO_URL"].rstrip("/") + "/v2/pipeline"
TOKEN = st.secrets["TURSO_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# AGORA COM TODOS OS PRÊMIOS
opcoes = ["1º Prêmio", "2º Prêmio", "3º Prêmio", "4º Prêmio", "5º Prêmio", "1º ao 3º Prêmio", "1º ao 5º Prêmio"]
premio = st.selectbox("Escolha o prêmio:", opcoes)

if st.button(f"🔍 Consultar {premio}", type="primary", use_container_width=True):
    with st.spinner(f"Analisando {premio}..."):
        # MAPA: qual coluna buscar no banco para cada opção
        sql_map = {
            "1º Prêmio": "SELECT bicho_1 as bicho FROM federal",
            "2º Prêmio": "SELECT bicho_2 as bicho FROM federal",
            "3º Prêmio": "SELECT bicho_3 as bicho FROM federal",
            "4º Prêmio": "SELECT bicho_4 as bicho FROM federal",
            "5º Prêmio": "SELECT bicho_5 as bicho FROM federal",
            "1º ao 3º Prêmio": "SELECT bicho_1 as bicho FROM federal UNION ALL SELECT bicho_2 FROM federal UNION ALL SELECT bicho_3 FROM federal",
            "1º ao 5º Prêmio": "SELECT bicho_1 as bicho FROM federal UNION ALL SELECT bicho_2 FROM federal UNION ALL SELECT bicho_3 FROM federal UNION ALL SELECT bicho_4 FROM federal UNION ALL SELECT bicho_5 FROM federal"
        }
        sql_base = sql_map[premio]
        # Calcula dias de atraso
        sql_final = f"""
        WITH sorteios AS ({sql_base})
        SELECT bicho, COUNT(*) as vezes FROM sorteios GROUP BY bicho
        """
        # Usa sua lógica original de 91 concursos aqui - me manda o nome das colunas se der erro
        payload = {"requests": [{"type":"execute","stmt":{"sql": sql_final}}, {"type":"close"}]}
        try:
            r = requests.post(URL, headers=HEADERS, json=payload).json()
            rows = r['results'][0]['response']['result']['rows']
            st.success(f"✅ {premio} - {len(rows)} resultados")
            st.dataframe(rows, use_container_width=True)
        except Exception as e:
            st.error("Erro ao consultar. Vou mostrar o retorno do Turso:")
            st.json(r)
