import streamlit as st
import requests
from datetime import datetime, date
import pandas as pd

st.set_page_config(page_title="Bicho Atrasado", page_icon="🎲", layout="centered")

if "auth" not in st.session_state: st.session_state.auth = False
if "admin_auth" not in st.session_state: st.session_state.admin_auth = False

if not st.session_state.auth:
    st.title("🔒 Área Restrita")
    senha = st.text_input("Senha de visualização:", type="password")
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
    return requests.post(URL, headers=H, json=payload).json()

def numero_para_bicho(num_str):
    try:
        n = int(str(num_str)[-2:])
        if n == 0: n = 100
        return (n - 1) // 4 + 1
    except: return None

def buscar_federal():
    # tenta direto na CAIXA primeiro, que é mais estável
    urls = [
        "https://servicebus2.caixa.gov.br/portaldeloterias/api/federal",
        "https://servicebus.caixa.gov.br/portaldeloterias/api/federal",
        "https://loteriascaixa-api.vercel.app/api/federal/latest",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            j = r.json()
            # Formato oficial da Caixa
            if "listaDezenas" in j and "dataApuracao" in j:
                return j["dataApuracao"], j["listaDezenas"][:5]
            # Formato vercel
            if "listaDezenas" in str(j).lower():
                data = j.get("dataApuracao") or j.get("data") or j.get("date")
                dezenas = j.get("listaDezenas") or j.get("dezenas")
                if data and dezenas:
                    premios = [d["numero"] if isinstance(d, dict) else str(d) for d in dezenas[:5]]
                    return data, premios
        except Exception as e:
            print(f"Falha {url}: {e}")
            continue
    return None, None

bancas_raw = query("SELECT id, nome FROM banca_sorteios ORDER BY nome")['rows']
bancas_list = [(int(r[0]['value']), r[1]['value']) for r in bancas_raw]
map_bancas = {id: nome for id, nome in bancas_list}

bichos_raw = query("SELECT id, nome FROM bicho ORDER BY id")['rows']
map_bicho = {int(r[0]['value']): r[1]['value'] for r in bichos_raw}

st.title("🎲 Bichos Atrasados")
tab1, tab2 = st.tabs(["📊 Consultar", "➕ Cadastrar Resultado"])

with tab1:
    banca_nomes = [f"{nome} (ID {bid})" for bid, nome in bancas_list]
    sel_banca_idx = st.selectbox("Escolha a BANCA:", banca_nomes, index=0)
    banca_id_sel = bancas_list[banca_nomes.index(sel_banca_idx)][0]
    opcoes = ["1º Prêmio", "2º Prêmio", "3º Prêmio", "4º Prêmio", "5º Prêmio", "1º ao 3º Prêmio", "1º ao 5º Prêmio"]
    premio_sel = st.selectbox("Escolha a consulta:", opcoes, index=5)
    if st.button(f"Consultar {premio_sel} - {map_bancas[banca_id_sel]}", type="primary", use_container_width=True):
        with st.spinner(f"Analisando {map_bancas[banca_id_sel]}..."):
            res = query(f"SELECT data, primeiro, segundo, terceiro, quarto, quinto FROM resultados WHERE banca_id={banca_id_sel} ORDER BY date(data) DESC LIMIT 365")
            linhas = res['rows']
            if not linhas:
                st.warning(f"Nenhum resultado para {map_bancas[banca_id_sel]}")
            else:
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
                    lista.append({"Bicho": f"{bicho_id:02d} - {nome}", "Dias": dias, "Concursos": concursos, "Última vez": ultima})
                        df = pd.DataFrame(lista).sort_values("Dias", ascending=False).reset_index(drop=True)
                        df.insert(0, "Col.", [f"{i+1}º" for i in range(len(df))])
                st.success(f"✅ {len(linhas)} concursos de {map_bancas[banca_id_sel]} - {premio_sel}")
                st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🔐 Cadastro - Admin")
    if not st.session_state.admin_auth:
        senha_admin = st.text_input("Senha ADMIN:", type="password", key="admin_pass")
        if st.button("Liberar Cadastro"):
            if senha_admin == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Senha admin incorreta!")
    else:
        st.success("Admin liberado!")
        with st.form("cadastro_manual"):
            banca_nomes_form = [f"{nome} (ID {bid})" for bid, nome in bancas_list]
            sel_banca_cad = st.selectbox("Banca do sorteio:", banca_nomes_form, index=0)
            banca_id_cad = bancas_list[banca_nomes_form.index(sel_banca_cad)][0]
            data_sorteio = st.date_input("Data do sorteio", value=date.today(), format="DD/MM/YYYY")
            st.write("Prêmios (ex: 1234)")
            c1, c2 = st.columns(2)
            p1 = c1.text_input("1º Prêmio*")
            p2 = c2.text_input("2º Prêmio*")
            p3 = c1.text_input("3º Prêmio*")
            p4 = c2.text_input("4º Prêmio*")
            p5 = c1.text_input("5º Prêmio*")
            if st.form_submit_button("💾 Salvar Manual", type="primary", use_container_width=True):
                if not all([p1,p2,p3,p4,p5]):
                    st.error("Preencha os 5 prêmios!")
                else:
                    check = query(f"SELECT id FROM resultados WHERE banca_id={banca_id_cad} AND data='{data_sorteio}'")['rows']
                    if check:
                        st.error(f"Já existe resultado para {map_bancas[banca_id_cad]} em {data_sorteio.strftime('%d/%m/%Y')}!")
                    else:
                        sql = f"INSERT INTO resultados (banca_id, data, primeiro, segundo, terceiro, quarto, quinto) VALUES ({banca_id_cad}, '{data_sorteio}', '{p1}', '{p2}', '{p3}', '{p4}', '{p5}')"
                        exec_sql(sql)
                        st.success(f"✅ Salvo! {map_bancas[banca_id_cad]} - {data_sorteio.strftime('%d/%m/%Y')}")
                        st.balloons()

        st.markdown("---")
        st.subheader("🤖 Atualização Automática - FEDERAL")
        if st.button("🔄 Buscar último resultado da Caixa"):
            data_caixa, premios = buscar_federal()
            if not data_caixa:
                st.error("APIs da Caixa estão fora agora. Use o cadastro manual.")
            else:
                try:
                    data_fmt = datetime.strptime(data_caixa[:10], "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    try:
                        data_fmt = datetime.strptime(data_caixa[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
                    except:
                        data_fmt = datetime.now().strftime("%Y-%m-%d")
                st.write(f"Encontrado: {data_caixa} - {premios}")
                check = query(f"SELECT id FROM resultados WHERE banca_id=1 AND data='{data_fmt}'")['rows']
                if check:
                    st.warning(f"Já cadastrado: {data_caixa}")
                else:
                    sql = f"INSERT INTO resultados (banca_id, data, primeiro, segundo, terceiro, quarto, quinto) VALUES (1, '{data_fmt}', '{premios[0]}', '{premios[1]}', '{premios[2]}', '{premios[3]}', '{premios[4]}')"
                    exec_sql(sql)
                    st.success(f"✅ Federal {data_caixa} salva automaticamente!")
                    st.balloons()

        if st.button("Sair do Admin"):
            st.session_state.admin_auth = False
            st.rerun()
