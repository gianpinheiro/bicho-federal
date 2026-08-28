import os, requests, socket, ssl, json
from datetime import datetime

TURSO_URL = os.environ["TURSO_URL"].rstrip("/") + "/v2/pipeline"
TURSO_TOKEN = os.environ["TURSO_TOKEN"]
H = {"Authorization": f"Bearer {TURSO_TOKEN}", "Content-Type": "application/json"}

def exec_sql(sql):
    payload = {"requests": [{"type":"execute","stmt":{"sql": sql}}]}
    r = requests.post(TURSO_URL, headers=H, json=payload, timeout=30)
    print(r.text[:500])
    return r.json()

def get_via_ip():
    try:
        print("Resolvendo servicebus.caixa.gov.br via 1.1.1.1...")
        r = requests.get(
            "https://1.1.1.1/dns-query",
            params={"name": "servicebus.caixa.gov.br", "type": "A"},
            headers={"accept": "application/dns-json", "Host": "cloudflare-dns.com"},
            verify=False, timeout=15
        )
        j = r.json()
        ips = [a["data"] for a in j.get("Answer", []) if a["type"]==1]
        print(f"IPs encontrados: {ips}")
        if not ips:
            return None
        for ip in ips:
            try:
                print(f"Tentando IP {ip}...")
                sock = socket.create_connection((ip, 443), timeout=15)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ssock = ctx.wrap_socket(sock, server_hostname="servicebus.caixa.gov.br")
                ssock.sendall(b"GET /portaldeloterias/api/federal HTTP/1.1\r\nHost: servicebus.caixa.gov.br\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n")
                resp = b""
                while True:
                    d = ssock.recv(8192)
                    if not d: break
                    resp += d
                ssock.close()
                body = resp.split(b"\r\n\r\n",1)[1]
                txt = body.decode('utf-8', errors='ignore')
                start = txt.find('{')
                end = txt.rfind('}')+1
                data = json.loads(txt[start:end])
                print(f"Pegou da CAIXA: {str(data)[:400]}")
                return data
            except Exception as e:
                print(f"Falha IP {ip}: {e}")
                continue
    except Exception as e:
        print(f"Erro get_via_ip: {e}")
    return None

data = get_via_ip()
if not data:
    print("Falhou")
    exit(1)

raw_date = data.get('dataApuracao') or data.get('data') or ""
lista = data.get('listaDezenas') or []
if "/" in str(raw_date):
    data_fmt = datetime.strptime(str(raw_date)[:10], "%d/%m/%Y").strftime("%Y-%m-%d")
else:
    data_fmt = datetime.strptime(str(raw_date)[:10], "%Y-%m-%d").strftime("%Y-%m-%d")

premios = [str(p).zfill(5)[-5:] for p in lista[:5]]
print(f"Resultado {data_fmt} - {premios}")

payload = {"requests":[{"type":"execute","stmt":{"sql": f"SELECT id FROM resultados WHERE banca_id=1 AND data='{data_fmt}'"}}]}
r = requests.post(TURSO_URL, headers=H, json=payload).json()
rows = r['results'][0]['response']['result']['rows']
if rows:
    print("Ja existe")
else:
    sql = f"INSERT INTO resultados (banca_id, data, primeiro, segundo, terceiro, quarto, quinto) VALUES (1, '{data_fmt}', '{premios[0]}','{premios[1]}','{premios[2]}','{premios[3]}','{premios[4]}')"
    exec_sql(sql)
    print("Salvo no Turso!")
