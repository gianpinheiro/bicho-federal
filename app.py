import requests
import streamlit as st
from datetime import datetime

# --- CONFIG ---
URL = "https://bichodb-gianpinheiro.aws-ap-northeast-1.turso.io/v2/pipeline"
TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODc4MzAxNDIsImlkIjoiMDFhMDNmODEtMjcwMS03ZDQ4LThlMTMtNmEwMGU3NzcyY2Y4Iiwia2lkIjoiOHR3Y1BvVzlHR0pHbFpoM1RZMm9ZOGJzX0poVnVDOEVEY2lmeG43MFVJWSIsInJpZCI6IjNhMjA0YzMwLWQyMzctNDllOC1iNzEyLWFiZmQ0MmEzOGFkZSJ9.UlOJQAAfgGzCJWH0ivGHm_iJdLQDS7fmx1SxOzNsRUWbLkT4RS2VIW6pR7WfHB930DUzb-yUFXI4kfJjpEHpAQ"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def dezena_to_bicho(dz):
    dz = int(dz)
    if dz == 0: dz = 100
    return (dz + 3) // 4

bichos_nome = {1:"Avestruz",2:"Águia",3:"Burro",4:"Borboleta",5:"Cachorro",6:"Cabra",7:"Carneiro",8:"Camelo",9:"Cobra",10:"Coelho",11:"Cavalo",12:"Elefante",13:"Galo",14:"Gato",15:"Jacaré",16:"Leão",17:"Macaco",18:"Porco",19:"Pavão",20:"Peru",21:"Touro",22:"Tigre",23:"Urso",24:"Veado",25:"Vaca"}

# --- SITE ---
st.set_page_config(page_title="Bicho Atraso - Federal", page_icon="🎲", layout="centered")
st.title("🎲 Consulta Bichos Atrasados - FEDERAL")

opcao = st.selectbox("Escolha o prêmio:", ["1º Prêmio (Cabeça)", "2º Prêmio", "3º Prêmio", "4º Prêmio", "5º Prêmio", "1º ao 3º Prêmio", "1º ao 5º Prêmio"])

mapa_sql = {
    "1º Prêmio (Cabeça)": "primeiro",
    "2º Prêmio": "segundo",
    "3º Prêmio": "terceiro",
    "4º Prêmio": "quarto",
    "5º Prêmio": "quinto",
    "1º ao 3º Prêmio": "primeiro, segundo, terceiro",
    "1º ao 5º Prêmio": "primeiro, segundo, terceiro, quarto, quinto"
}

coluna_sql = mapa_sql[opcao]
sql = f"SELECT data, {coluna_sql} FROM resultados WHERE banca_id=(SELECT id FROM banca_sorteios WHERE nome='FEDERAL') ORDER BY data ASC;"

if st.button(f"Consultar {opcao}"):
    with st.spinner("Buscando no banco..."):
        resp = requests.post(URL, headers=headers, json={"requests": [{"type": "execute", "stmt": {"sql": sql}}, {"type": "close"}]}).json()
        rows = resp['results'][0]['response']['result']['rows']

        sorteios = []
        for r in rows:
            data = r[0]['value']
            milhares = [r[i]['value'] for i in range(1, len(r))]
            sorteios.append((data, milhares))

        ultima_aparicao = {}
        for idx, (data_str, milhares) in enumerate(sorteios):
            data = datetime.strptime(data_str, "%Y-%m-%d")
            for milhar in milhares:
                if not milhar: continue
                bicho = dezena_to_bicho(int(str(milhar)[-2:]))
                ultima_aparicao[bicho] = (data, idx)

        ultimo_sorteio = datetime.strptime(sorteios[-1][0], "%Y-%m-%d")
        ultimo_indice = len(sorteios) - 1

        resultado = []
        for b_id in range(1,26):
            if b_id in ultima_aparicao:
                ultima_data, ultimo_idx_bicho = ultima_aparicao[b_id]
                dias = (ultimo_sorteio - ultima_data).days
                concursos = ultimo_indice - ultimo_idx_bicho
                resultado.append({"BICHO": f"{b_id:02d}-{bichos_nome[b_id]}", "ULTIMA": ultima_data.strftime('%d/%m/%Y'), "DIAS": dias, "CONCURSOS": concursos})

        resultado = sorted(resultado, key=lambda x: x["CONCURSOS"], reverse=True)

        st.success(f"Último sorteio: {ultimo_sorteio.strftime('%d/%m/%Y')} - {len(sorteios)} concursos analisados")
        st.dataframe(resultado, use_container_width=True, hide_index=True)