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
    urls = [
        "https://caixa.gov.br",
        "https://caixa.gov.br",
        "https://vercel.app",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            j = r.json()
            if "listaDezenas" in j and "dataApuracao" in j:
                return j["dataApuracao"], j["listaDezenas"][:5]
            if "listaDezenas" in str(j).lower():
                data = j.get("dataApuracao") or j.get("data") or j.get("date")
                dezenas = j.get("listaDezenas") or j.get("dezenas")
                if data and dezenas:
                    premios = [d["numero"] if isinstance(d, dict) else str(d) for d in dezenas[:5]]
                    return data, premios
        except: continue
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
    
    # ADICIONADO: Opção para ver o resultado exato do dia selecionado
    opcoes = [
        "Ver Resultado do Dia",
        "1º Prêmio", 
        "2º Prêmio", 
        "3º Prêmio", 
        "4º Prêmio", 
        "5º Prêmio", 
        "1º ao 3º Prêmio", 
        "1º ao 5º Prêmio"
    ]
    premio_sel = st.selectbox("Escolha a consulta:", opcoes, index=0)

    # Campo de digitação/seleção da data desejada
    data_limite = st.date_input("Escolha a data da consulta:", value=date.today())
    data_limite_str = data_limite.strftime("%Y-%m-%d")

    c_a, c_b = st.columns([3, 1.5])
    with c_a:
        btn_consultar = st.button(f"Executar Consulta", type="primary", use_container_width=True)
    with c_b:
        btn_ultimo = st.button("👁️ Último jogo", use_container_width=True)

    # Ação do botão de Ver Último Jogo (Mantido até a data estipulada)
    if btn_ultimo:
        ult = query(f"SELECT data, primeiro, segundo, terceiro, quarto, quinto FROM resultados WHERE banca_id={banca_id_sel} AND date(data) <= date('{data_limite_str}') ORDER BY date(data) DESC LIMIT 1")['rows']
        if not ult:
            st.warning(f"Nenhum jogo cadastrado para {map_bancas[banca_id_sel]} até {data_limite.strftime('%d/%m/%Y')}")
        else:
            l = ult[0]
            data_ult = l[0]['value']
            try:
                data_formatada = datetime.strptime(data_ult, "%Y-%m-%d").strftime("%d/%m/%Y")
                dt_obj = datetime.strptime(data_ult, "%Y-%m-%d")
            except:
                data_formatada = data_ult
                dt_obj = datetime.now()

            dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
            dia_semana = dias_semana[dt_obj.weekday()]

            st.markdown(f'<div style="text-align:center; background-color:#e3f2fd; padding:12px; border-radius:8px; margin-bottom:12px; font-weight:bold; color:#0d47a1; font-size:16px;">Último Sorteio considerado: {map_bancas[banca_id_sel]} - {data_formatada} ({dia_semana})</div>', unsafe_allow_html=True)

            premios = [l[1]['value'], l[2]['value'], l[3]['value'], l[4]['value'], l[5]['value']]
            html = '<div style="text-align:center; background-color:#ffffff; padding:20px; border-radius:12px; border:1px solid #dee2e6; line-height:2.4;">'
            for i, milhar in enumerate(premios, start=1):
                b_id = numero_para_bicho(milhar)
                b_nome = map_bicho.get(b_id, "Desconhecido")
                milhar_4 = str(milhar)[-4:].zfill(4)
                html += f'<div style="font-size:16px;"><b>{i}º Prêmio - {milhar_4} - {b_nome}</b></div>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

    # Ação principal do botão Consultar
    if btn_consultar:
        # NOVA CONDICIONAL: Se escolheu ver o resultado exato daquele dia digitado
        if premio_sel == "Ver Resultado do Dia":
            with st.spinner(f"Buscando resultado de {data_limite.strftime('%d/%m/%Y')}..."):
                res_dia = query(f"SELECT data, primeiro, segundo, terceiro, quarto, quinto FROM resultados WHERE banca_id={banca_id_sel} AND date(data) = date('{data_limite_str}') LIMIT 1")['rows']
                
                if not res_dia:
                    st.error(f"❌ Nenhum sorteio cadastrado para a banca {map_bancas[banca_id_sel]} no dia {data_limite.strftime('%d/%m/%Y')}.")
                else:
                    l = res_dia[0]
                    dt_obj = datetime.strptime(l[0]['value'], "%Y-%m-%d")
                    dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                    dia_semana = dias_semana[dt_obj.weekday()]

                    st.markdown(f'<div style="text-align:center; background-color:#e8f5e9; padding:12px; border-radius:8px; margin-bottom:12px; font-weight:bold; color:#1b5e20; font-size:16px;">Resultado Encontrado: {map_bancas[banca_id_sel]} - {data_limite.strftime("%d/%m/%Y")} ({dia_semana})</div>', unsafe_allow_html=True)

                    premios = [l[1]['value'], l[2]['value'], l[3]['value'], l[4]['value'], l[5]['value']]
                    html = '<div style="text-align:center; background-color:#ffffff; padding:20px; border-radius:12px; border:1px solid #dee2e6; line-height:2.4;">'
                    for i, milhar in enumerate(premios, start=1):
                        b_id = numero_para_bicho(milhar)
                        b_nome = map_bicho.get(b_id, "Desconhecido")
                        milhar_4 = str(milhar)[-4:].zfill(4)
                        html += f'<div style="font-size:16px;"><b>{i}º Prêmio - {milhar_4} - {b_nome}</b></div>'
                    html += '</div>'
                    st.markdown(html, unsafe_allow_html=True)
        
        # Comportamento antigo: Calcula a tabela de estatísticas de bichos atrasados
        else:
            with st.spinner(f"Analisando {map_bancas[banca_id_sel]}..."):
                res = query(f"SELECT data, primeiro, segundo, terceiro, quarto, quinto FROM resultados WHERE banca_id={banca_id_sel} AND date(data) <= date('{data_limite_str}') ORDER BY date(data) DESC LIMIT 365")
                linhas = res['rows']
                if not linhas:
                    st.warning(f"Nenhum resultado para {map_bancas[banca_id_sel]} até a data selecionada.")
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
                    
                    data_base_calculo = datetime.combine(data_limite, datetime.min.time())
                    lista = []
                    for bicho_id in range(1, 26):
                        nome = map_bicho.get(bicho_id, f"Bicho {bicho_id}")
                        info = ultima_info.get(bicho_id)
                        if info:
                            dias = (data_base_calculo - info["data"]).days
                            concursos = info["concursos"]
                            ultima = info["data"].strftime("%d/%m/%Y")
                        else:
                            dias = 999
                            concursos = len(linhas)
                            ultima = "Nunca"
