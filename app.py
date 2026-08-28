import streamlit as st
import requests
from datetime import datetime
import pandas as pd

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

URL = st.secrets["TURSO_URL"].rstrip("/") + "/v2/pipeline"
TOKEN = st.secrets["TURSO_TOKEN"]
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def query(sql):
    payload = {"requests": [{"type":"execute","stmt":{"sql": sql}}]}
    r = requests.post(URL, headers=H, json=payload).json()
    return r['results'][0]['response']['result']

def numero_para_bicho(num_str):
    try:
        n = int(str(num_str)[-2:]) # pega 2 ultimos digitos
        if n == 0:
            n = 100
        return (n - 1) // 4 + 1
    except:
        return None

# Carrega bichos
bichos_raw = query("SELECT id, nome FROM bicho ORDER BY id")['rows']
map_bicho = {int(r[0]['value']): r[1]['value'] for r in bichos_raw}

st.title("🎲 Bichos Atrasados - FEDERAL")
st.caption("Banco: resultados / banca_id = 1 (FEDERAL)")

opcoes = ["1º Prêmio", "2º Prêmio", "3º Prêmio", "4º Prêmio", "5º Prêmio", "1º ao 3º Prêmio", "1º ao 5º Prêmio"]
premio_sel = st.selectbox("Escolha a consulta:", opcoes, index=6)

if st.button(f"Consultar {premio_sel}", type="primary", use_container_width=True):
    with st.spinner("Buscando resultados da Federal..."):
        # Pega ultimos 365 sorteios da federal
        res = query("SELECT data, primeiro, segundo, terceiro, quarto, quinto FROM resultados WHERE banca_id=1 ORDER BY date(data) DESC LIMIT 365")
        linhas = res['rows']

        # Mapeia o que consultar
        idx_map = {"1º Prêmio":[0], "2º Prêmio":[1], "3º Prêmio":[2], "4º Prêmio":[3], "5º Prêmio":[4], "1º ao 3º Prêmio":[0,1,2], "1º ao 5º Prêmio":[0,1,2,3,4]}
        idxs = idx_map[premio_sel]

        # Ultima vez que cada bicho saiu
        ultima_data = {}
        for linha in linhas:
            data_str = linha[0]['value']
            numeros = [linha[1]['value'], linha[2]['value'], linha[3]['value'], linha[4]['value'], linha[5]['value']]
            for i in idxs:
                b = numero_para_bicho(numeros[i])
                if b and b not in ultima_data:
                    # primeira vez que encontra de tras pra frente = mais recente
                    try:
                        ultima_data[b] = datetime.strptime(data_str, "%Y-%m-%d")
                    except:
                        ultima_data[b] = datetime.now()

        hoje = datetime.now()
        lista = []
        for bicho_id in range(1, 26):
            nome = map_bicho.get(bicho_id, f"Bicho {bicho_id}")
            if bicho_id in ultima_data:
                dias = (hoje - ultima_data[bicho_id]).days
                ultima = ultima_data[bicho_id].strftime("%d/%m/%Y")
            else:
                dias = 999
                ultima = "Nunca"
            lista.append({"Bicho": f"{bicho_id:02d} - {nome}", "Dias Atrasado": dias, "Última vez": ultima})

        df = pd.DataFrame(lista).sort_values("Dias Atrasado", ascending=False)
        st.success(f"✅ {len(linhas)} concursos analisados - {premio_sel}")
        st.dataframe(df, use_container_width=True, hide_index=True)

st.info("Dica: 07-Carneiro 67 dias = faz 67 dias que o Carneiro não sai nesse prêmio")
