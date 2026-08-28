import requests, os
from datetime import datetime

TURSO_URL = os.environ["TURSO_URL"].rstrip("/") + "/v2/pipeline"
TURSO_TOKEN = os.environ["TURSO_TOKEN"]
H = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}

def query(sql):
    payload = {"requests": [{"type":"execute","stmt":{"sql": sql}}]}
    r = requests.post(TURSO_URL, headers=H, json=payload).json()
    return r['results'][0]['response']['result']

def exec_sql(sql):
    payload = {"requests": [{"type":"execute","stmt":{"sql": sql}}]}
    return requests.post(TURSO_URL, headers=H, json=payload).json()

url = "https://servicebus.caixa.gov.br/portaldeloterias/api/federal"
data = requests.get(url, timeout=15).json()
data_caixa = data['dataApuracao']
data_fmt = datetime.strptime(data_caixa, "%d/%m/%Y").strftime("%Y-%m-%d")
premios = [p['numero'] for p in data['listaDezenas'][:5]]

print(f"Resultado {data_caixa} - {premios}")

check = query(f"SELECT id FROM resultados WHERE banca_id=1 AND data='{data_fmt}'")['rows']
if not check:
    sql = f"INSERT INTO resultados (banca_id, data, primeiro, segundo, terceiro, quarto, quinto) VALUES (1, '{data_fmt}', '{premios[0]}', '{premios[1]}', '{premios[2]}', '{premios[3]}', '{premios[4]}')"
    exec_sql(sql)
    print("Salvo no Turso!")
else:
    print("Ja existe no banco")
