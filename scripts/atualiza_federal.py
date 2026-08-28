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

urls = [
    "https://servicebus.caixa.gov.br/portaldeloterias/api/federal",
    "https://loteriascaixa-api.herdapps.com.br/api/federal/ultimo",
    "https://api.guidi.dev.br/loteria/federal/ultimo"
]

data = None
for url in urls:
    try:
        print(f"Tentando {url}")
        r = requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code == 200:
            j = r.json()
            if isinstance(j, list):
                j = j[0]
            data = j
            print(f"OK em {url}")
            break
    except Exception as e:
        print(f"Falhou {url}: {e}")

if not data:
    print("Todas APIs falharam")
    exit(1)

# tenta extrair data e premios de qualquer formato
try:
    data_caixa = data.get('dataApuracao') or data.get('data') or data.get('dataConcurso') or ""
    # alguns vem com 2025-08-27
    if "/" in data_caixa:
        data_fmt = datetime.strptime(data_caixa, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        data_fmt = datetime.strptime(data_caixa[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
except:
    data_fmt = datetime.now().strftime("%Y-%m-%d")

# extrai os 5 premios
premios = []
lista = data.get('listaDezenas') or data.get('dezenas') or data.get('numeros') or []
for p in lista[:5]:
    if isinstance(p, dict):
        premios.append(str(p.get('numero') or p.get('dezena') or p))
    else:
        premios.append(str(p))

print(f"Resultado {data_fmt} - {premios}")

if len(premios) < 5:
    print(f"Erro: veio incompleto {premios}")
    exit(1)

check = query(f"SELECT id FROM resultados WHERE banca_id=1 AND data='{data_fmt}'")['rows']
if not check:
    sql = f"INSERT INTO resultados (banca_id, data, primeiro, segundo, terceiro, quarto, quinto) VALUES (1, '{data_fmt}', '{premios[0]}', '{premios[1]}', '{premios[2]}', '{premios[3]}', '{premios[4]}')"
    exec_sql(sql)
    print("Salvo no Turso!")
else:
    print("Ja existe no banco")
