#... mantém tudo que você já tem, só ADICIONA isso dentro da tab2 admin:

import requests as rq

# dentro do with tab2: depois do form manual, adiciona:

st.divider()
st.subheader("🤖 Atualização Automática - FEDERAL")

if st.button("🔄 Buscar último resultado da Caixa e salvar"):
    try:
        # API pública da Caixa
        url_caixa = "https://servicebus.caixa.gov.br/portaldeloterias/api/federal"
        res_caixa = rq.get(url_caixa, timeout=10).json()

        # pega os 5 primeiros prêmios
        data_caixa = res_caixa['dataApuracao'] # ex: 26/08/2026
        data_formatada = datetime.strptime(data_caixa, "%d/%m/%Y").strftime("%Y-%m-%d")
        premios = [p['numero'] for p in res_caixa['listaDezenas'][:5]]

        st.write(f"Resultado encontrado: {data_caixa} - {premios}")

        # verifica se já existe
        check = query(f"SELECT id FROM resultados WHERE banca_id=1 AND data='{data_formatada}'")['rows']
        if check:
            st.warning(f"Já cadastrado: {data_caixa}")
        else:
            sql = f"INSERT INTO resultados (banca_id, data, primeiro, segundo, terceiro, quarto, quinto) VALUES (1, '{data_formatada}', '{premios[0]}', '{premios[1]}', '{premios[2]}', '{premios[3]}', '{premios[4]}')"
            exec_sql(sql)
            st.success(f"✅ Federal {data_caixa} salva automaticamente!")
            st.balloons()
    except Exception as e:
        st.error(f"Erro ao buscar na Caixa: {e}")
        st.info("Tenta o cadastro manual se a API da Caixa estiver fora.")
