import requests, os, socket
from datetime import datetime
import json

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

def get_with_doh(host, path):
    # 1. tenta pegar IP via Cloudflare DNS
    try:
        doh = requests.get(f"https://cloudflare-dns.com/dns-query?name={host}&type=A",
                            headers={"accept":"application/dns-json"}, timeout=10).json()
        ip = doh['Answer'][0]['data']
        print(f"DNS DOH {host} -> {ip}")
        # 2. busca usando IP mas com Host header
        url_ip = f"https://{ip}{path}"
        r = requests.get(url_ip, headers={"Host": host, "User-Agent":"Mozilla/5.0"}, verify=False, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"DOH falhou {host}: {e}")
    return None

targets = [
    ("servicebus.caixa.gov.br", "/portaldeloterias/api/federal"),
    ("loteriascaixa-api.herdapps.com.br", "/api/federal/ultimo"),
    ("api.guidi.dev.br", "/loteria/federal/ultimo")
]

data = None
for host, path in targets:
    print(f"Tentando {host}")
    # tenta normal
    try:
        r = requests.get(f"https://{host}{path}", timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code == 200:
            j = r.json()
            if isinstance(j, list): j = j[0]
            data = j
            print(f"OK normal em {host}")
            break
    except Exception as e:
        print(f"Normal falhou, tentando DOH")

    # tenta via DOH
    j = get_with_doh(host, path)
    if j:
        if isinstance(j, list): j = j[0]
        data = j
        break

if not data:
    print("Todas APIs falharam")
    exit(1)

print(f"Dados: {str(data)[:600]}")

try:
    data_caixa = data.get('dataApuracao') or data.get('data') or data.get('dataConcurso') or ""
    if "/" in data_caixa:
        data_fmt = datetime.strptime(data_caixa, "%d/%m/%Y").strftime("%Y-%m-%d")
    else:
        data_fmt = datetime.strptime(data_caixa[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
except:
    data_fmt = datetime.now().strftime("%Y-%m-%d")

premios = []
lista = data.get('listaDezenas') or data.get('dezenas') or data.get('numeros') or []
for p in lista[:5]:
    if isinstance(p, dict):
        premios.append(str(p.get('numero') or p.get('dezena') or p))
    else:
        premios.append(str(p))

print(f"Resultado {data_fmt} - {premios}")

if len(premios) < 5:
    exit(1)

check = query(f"SELECT id FROM resultados WHERE banca_id=1 AND data='{data_fmt}'")['rows']
if not check:
    sql = f"INSERT INTO resultados (banca_id, data, primeiro, segundo, terceiro, quarto, quinto) VALUES (1, '{data_fmt}', '{premios[0]}', '{premios[1]}', '{premios[2]}', '{premios[3]}', '{premios[4]}')"
    exec_sql(sql)
    print("Salvo no Turso!")
else:
    print("Ja existe no banco")
