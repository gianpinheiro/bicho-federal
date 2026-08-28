import requests, os, sys

TURSO_URL = os.getenv("TURSO_URL")
TURSO_TOKEN = os.getenv("TURSO_TOKEN")

urls = [
    "https://servicebus.caixa.gov.br/portaldeloterias/api/federal",
    "https://loteriascaixa-api.herdapps.com.br/api/federal/ultimo",
    "https://api.guidi.dev.br/loteria/federal/ultimo"
]

data = None
for url in urls:
    try:
        print(f"Tentando {url}")
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"OK em {url}")
            break
    except Exception as e:
        print(f"Falhou {url}: {e}")
        continue

if not data:
    print("Todas APIs falharam")
    sys.exit(1)

# adapta formato
if isinstance(data, list):
    data = data[0]

print(f"Concurso: {data}")
# aqui continua seu codigo que salva no Turso...
# mantenha o resto que insere no banco
