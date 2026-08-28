import streamlit as st
import requests
from datetime import datetime, date
import pandas as pd

st.set_page_config(page_title="Bicho Atrasado - Federal", page_icon="🎲", layout="centered")

# --- SENHA DE VISUALIZAÇÃO ---
if "auth" not in st.session_state:
    st.session_state.auth = False
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

if not st.session_state.auth:
    st.title("🔒 Área Restrita")
    senha = st.text_input("Digite a senha de visualização:", type="password")
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

def exec_sql(sql):
    payload = {"requests": [{"type":"execute","stmt":{"sql": sql}}]}
    r = requests.post(URL, headers=H, json=payload).json()
    return r

def numero_para_bicho(num_str):
    try:
        n = int(str(num_str)[-2:])
        if n == 0: n = 100
        return (n - 1) // 4 + 1
    except:
        return None

bichos_raw = query("SELECT id, nome FROM bicho ORDER BY id")['rows']
map_bicho = {int(r[0]['value']): r[1]['value'] for r in bichos_raw}

# --- MENU ---
st.title("🎲 Bichos Atrasados - FEDERAL")
tab1, tab2 = st.tabs(["📊 Consultar", "➕ Cadastrar Resultado"])

with tab1:
    st.caption("Banco: resultados / banca_id = 1 (FEDERAL)")
    opcoes = ["1º Prêmio", "2º Prêmio", "3º Prêmio", "4º Prêmio", "5º Prêmio", "1º ao 3º Prêmio", "1º ao 5º Prêmio"]
    premio_sel = st.selectbox("Escolha a consulta:", opcoes, index=5)

    if st.button(f"Consultar {premio_sel}", type="primary", use_container_width=True):
        with st.spinner(f"Analisando {premio_sel}..."):
            res = query("SELECT data, primeiro, segundo, terceiro, quarto, quinto FROM resultados WHERE banca_id=1 ORDER BY date(data) DESC LIMIT 365")
            linhas = res['rows']
            idx_map = {"1º Prêmio":[0], "2º Prêmio":[1], "3º Prêmio":[2], "4º Prêmio":[3], "5º Prêmio":[4], "1º ao 3º Prêmio":[0,1,2], "1º ao 5º Prêmio":[0,1,2,3,4]}
            idxs = idx_map[premio_sel]
            ultima_info = {}
            for pos, linha in enumerate(linhas):
                data_str = linha[0]['value']
                numeros = [linha[1]['value'], linha[2]['value'], linha[3]['value'], linha[4]['value'], linha[5]['value']]
                for i in idxs:
                    b = numero_para_bicho(numeros[i])
                    if b and b not in ultima_info:
                        try: dt = datetime.strptime(data_str, "%Y-%m-%d")
                        except: dt = datetime.now()
                        ultima_info[b] = {"data": dt, "concursos": pos}
            hoje = datetime.now()
            lista = []
            for bicho_id in range(1, 26):
                nome = map_bicho.get(bicho_id, f"Bicho {bicho_id}")
                info = ultima_info.get(bicho_id)
                if info:
                    dias = (hoje - info["data"]).days
                    concursos = info["concursos"]
                    ultima = info["data"].strftime("%d/%m/%Y")
                else:
                    dias = 999; concursos = len(linhas); ultima = "Nunca"
                lista.append({"Bicho": f"{bicho_id:02d} - {nome}", "Dias Atrasado": dias, "Concursos Atrasados": concursos, "Última vez": ultima})
            df = pd.DataFrame(lista).sort_values("Dias Atrasado", ascending=False)
            st.success(f"✅ {len(linhas)} concursos analisados - {premio_sel}")
            st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🔐 Área Admin - Lançar Resultado")
    if not st.session_state.admin_auth:
        senha_admin = st.text_input("Digite a senha de ADMIN:", type="password")
        if st.button("Liberar Cadastro"):
            if senha_admin == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Senha admin incorreta!")
    else:
        st.success("Admin liberado!")
        with st.form("cadastro"):
            data_sorteio = st.date_input("Data do sorteio", value=date.today(), format="DD/MM/YYYY")
            st.write("Digite os 5 prêmios (só números, ex: 1234)")
            c1, c2 = st.columns(2)
            p1 = c1.text_input("1º Prêmio*")
            p2 = c2.text_input("2º Prêmio*")
            p3 = c1.text_input("3º Prêmio*")
            p4 = c2.text_input("4º Prêmio*")
            p5 = c1.text_input("5º Prêmio")

            if st.form_submit_button("💾 Salvar Resultado", type="primary", use_container_width=True):
                if not p1 or not p2 or not p3 or not p4 or not p5:
                    st.error("Preencha todos os 5 prêmios!")
                else:
                    # Verifica se já existe nessa data
                    check = query(f"SELECT id FROM resultados WHERE banca_id=1 AND data='{data_sorteio}'")['rows']
                    if check:
                        st.error(f"Já existe resultado para {data_sorteio.strftime('%d/%m/%Y')}!")
                    else:
                        sql = f"INSERT INTO resultados (banca_id, data, primeiro, segundo, terceiro, quarto, quinto) VALUES (1, '{data_sorteio}', '{p1}', '{p2}', '{p3}', '{p4}', '{p5}')"
                        resp = exec_sql(sql)
                        if 'error' in str(resp).lower():
                            st.error(f"Erro: {resp}")
                        else:
                            st.success(f"✅ Resultado de {data_sorteio.strftime('%d/%m/%Y')} salvo! Atualize a aba Consultar.")
                            st.balloons()
        if st.button("Sair do Admin"):
            st.session_state.admin_auth = False
            st.rerun()
