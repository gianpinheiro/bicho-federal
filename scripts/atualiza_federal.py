import requests, os
from datetime import datetime

TURSO_URL = os.environ["TURSO_URL"].rstrip("/") + "/v2/pipeline"
TURSO_TOKEN = os.environ["TURSO_TOKEN"]
H = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}

def exec_sql(sql):
    payload = {"requests": [{"type":"execute","stmt":{"sql": sql}}]}
    r = requests.post(TURSO_URL, headers=H, json=payload)
    print(r.text[:500])
    return r.json()

def tenta(url):
    try:
        print(f"GET {url}")
        r = requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
        print(f"Status {r.status_code}")
        if r.status_code == 200:
            j = r.json()
            return j[0] if isinstance(j, list) else j
    except Exception as e:
        print(f"Erro {e}")
    return None

# ORDEM: primeiro as que funcionam no Actions (vercel)
urls = [
    "https://loteriascaixa-api.vercel.app/api/federal/latest",
    "https://loterica.vercel.app/api/federal/latest",
    "https://api-loterias.herokuapp.com/api/v1/federal/ultimo",
    "https://thingproxy.freeboard.io/fetch/https://servicebus.caixa.gov.br/portaldeloterias/api/federal",
    "https://api.codetabs.com/v1/proxy?quest=https://servicebus.caixa.gov.br/portaldeloterias/api/federal",
]

data = None
for u in urls:
    j = tenta(u)
    if j:
        # algumas APIs vem embrulhadas em {data: {...}}
        if "data" in j and isinstance(j["data"], dict) and "listaDezenas" in str(j["data"]):
            j = j["data"]
        if "listaDezenas" in str(j) or "dezenas" in j:
            data = j
            print(f"ACHOU EM {u}")
            break

if not data:
    print("Todas APIs falharam")
    exit(1)

raw_date = data.get('dataApuracao') or data.get('data') or data.get('dataConcurso') or ""
lista = data.get('listaDezenas') or data.get('dezenas') or []

if "/" in str(raw_date):
    data_fmt = datetime.strptime(str(raw_date)[:10], "%d/%m/%Y").strftime("%Y-%m-%d")
else:
    data_fmt = datetime.strptime(str(raw_date)[:10], "%Y-%m-%d").strftime("%Y-%m-%d")

premios = [str(p if isinstance(p,str) else p.get('numero','')).zfill(5)[-5:] for p in lista[:5]]
print(f"Resultado {data_fmt} - {premios}")

if len(premios) < 5:
    exit(1)

# verifica se ja existe
payload = {"requests":[{"type":"execute","stmt":{"sql": f"SELECT id FROM resultados WHERE banca_id=1 AND data='{data_fmt}'"}}]}
r = requests.post(TURSO_URL, headers=H, json=payload).json()
rows = r['results'][0]['response']['result']['rows']
if rows:
    print("Ja existe no banco")
else:
    sql = f"INSERT INTO resultados (banca_id, data, primeiro, segundo, terceiro, quarto, quinto) VALUES (1, '{data_fmt}', '{premios[0]}', '{premios[1]}', '{premios[2]}', '{premios[3]}', '{premios[4]}')"
    exec_sql(sql)
    print("Salvo no Turso!")
