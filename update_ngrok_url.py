import os
import json
import re
import requests
from pathlib import Path

# Token de prueba (Sandbox)
MP_ACCESS_TOKEN_SANDBOX = "TEST-7429934597752386-052722-2b3af6cbfe000d172d6b847019a36d3d-2464461320"

# Token de Producción (descomentar cuando se pase a producción)
# MP_ACCESS_TOKEN_PROD = "APP_USR-8742947522442677-060223-396c1153906822a73b663c752f0baf33-2461175817"

# URL base para Webhooks
MP_API_BASE = "https://api.mercadopago.com/v1/webhooks"

# IDs de planes en Sandbox 
PLAN_IDS = [
    "2c938084970fb5df01972e615a200bcb",  # Plan Oro 
    "2c93808497271d1901972e62675a0211",  # Plan Plata 
]

# Lista de eventos para recibir en el Webhook
WEBHOOK_TOPICS = ["payment", "preapproval"]

# Ruta a settings.py 
SETTINGS_PATH = Path("Alpatex/settings.py")

# Nombre de la variable en settings.py
NGROK_VAR_NAME = "NGROK_URL"

#Consulta el API local de ngrok para obtener el túnel HTTPS
# Devuelve una URL como 'https://abcd1234.ngrok.io' o None si falla
def get_ngrok_url():
    try:
        r = requests.get("http://localhost:4040/api/tunnels")
        r.raise_for_status()
        data = r.json()
        for t in data.get("tunnels", []):
            if t.get("proto") == "https":
                return t.get("public_url")
    except Exception as e:
        print("Error obteniendo la URL de ngrok:", e)
    return None

#inserta o reemplaza la línea NGROK_URL = 'ngrok_url' en settings.py
#Actualiza ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS para incluir el dominio de ngrok
def update_settings(ngrok_url: str):
    if not SETTINGS_PATH.exists():
        print(f"No se encontró el archivo {SETTINGS_PATH}")
        return

    content = SETTINGS_PATH.read_text(encoding="utf-8")
    
    # Actualizar NGROK_URL
    ngrok_pattern = rf"{NGROK_VAR_NAME}\s*=\s*['\"].*?['\"]"
    nuevo_ngrok = f"{NGROK_VAR_NAME} = '{ngrok_url}'"

    if re.search(ngrok_pattern, content):
        content = re.sub(ngrok_pattern, nuevo_ngrok, content)
    else:
        content += f"\n\n# URL pública de ngrok (se actualiza automáticamente)\n{nuevo_ngrok}\n"

    # Extraer el dominio de ngrok (sin el protocolo)
    ngrok_domain = ngrok_url.replace('https://', '').replace('http://', '')
    
    # actualizar ALLOWED_HOSTS
    hosts_pattern = r"ALLOWED_HOSTS\s*=\s*\[(.*?)\]"
    hosts_match = re.search(hosts_pattern, content, re.DOTALL)
    
    if hosts_match:
        current_hosts = hosts_match.group(1)
        # Convertir la lista actual a un conjunto para evitar duplicados
        hosts_set = {h.strip().strip("'\"") for h in current_hosts.split(',') if h.strip()}
        # Agregar el nuevo dominio y los hosts locales si no existen
        hosts_set.update([ngrok_domain, 'localhost', '127.0.0.1'])
        # Convertir de vuelta a una lista ordenada
        hosts_list = sorted(list(hosts_set))
        new_hosts = f"ALLOWED_HOSTS = [{', '.join(repr(h) for h in hosts_list)}]"
        content = re.sub(hosts_pattern, new_hosts, content)
    else:
        # Si no existe ALLOWED_HOSTS, agregarlo después de DEBUG
        debug_pattern = r"(DEBUG\s*=\s*True)"
        new_hosts = f"\\1\n\nALLOWED_HOSTS = ['{ngrok_domain}', 'localhost', '127.0.0.1']"
        content = re.sub(debug_pattern, new_hosts, content)

    # Actualizar CSRF_TRUSTED_ORIGINS
    csrf_pattern = r"CSRF_TRUSTED_ORIGINS\s*=\s*\[(.*?)\]"
    csrf_match = re.search(csrf_pattern, content, re.DOTALL)
    
    if csrf_match:
        current_origins = csrf_match.group(1)
        # Convertir la lista actual a un conjunto para evitar duplicados
        origins_set = {o.strip().strip("'\"") for o in current_origins.split(',') if o.strip()}
        # Agregar el nuevo origen
        origins_set.add(ngrok_url)
        # Convertir de vuelta a una lista ordenada
        origins_list = sorted(list(origins_set))
        new_csrf = f"CSRF_TRUSTED_ORIGINS = [{', '.join(repr(o) for o in origins_list)}]"
        content = re.sub(csrf_pattern, new_csrf, content)
    else:
        # Si no existe CSRF_TRUSTED_ORIGINS, agregarlo después de ALLOWED_HOSTS
        hosts_pattern = r"(ALLOWED_HOSTS\s*=\s*\[.*?\])"
        new_csrf = f"\\1\n\nCSRF_TRUSTED_ORIGINS = ['{ngrok_url}']"
        content = re.sub(hosts_pattern, new_csrf, content, flags=re.DOTALL)

    SETTINGS_PATH.write_text(content, encoding="utf-8")
    print(f"settings.py actualizado:")
    print(f"- {NGROK_VAR_NAME} = '{ngrok_url}'")
    print(f"- ALLOWED_HOSTS actualizado para incluir '{ngrok_domain}'")
    print(f"- CSRF_TRUSTED_ORIGINS actualizado para incluir '{ngrok_url}'")


#Lista todos los webhooks del entorno
# retorna la lista de objetos. si no hay ninguno (404), devuelve lista vacia
#si ocurre otro error, retorna None
def list_webhooks(access_token: str):
    url = MP_API_BASE
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        print(f"Intentando listar webhooks en {url}")
        print(f"Usando token: {access_token[:10]}...")
        r = requests.get(url, headers=headers)
        print(f"Respuesta del servidor: {r.status_code}")

        # En Sandbox, si no existe ningun webhook, Mercado Pago devuelve 404
        if r.status_code == 404:
            print("No hay webhooks existentes. Se interpretará como lista vacía.")
            return []

        r.raise_for_status()
        payload = r.json()
        return payload.get("data", [])
    except Exception as e:
        print(f"Error listando webhooks (token={access_token[:10]}...): {e}")
        return None

#crea un nuevo webhook, devuelve el json completo de respuesta si se crea con exito, o None si falla
def create_webhook(access_token: str, target_url: str, topics: list):
    url = MP_API_BASE
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    body = {
        "url": target_url,
        "topics": topics
    }

    try:
        print(f"Creando webhook en {url} → URL destino: {target_url}")
        r = requests.post(url, json=body, headers=headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error creando webhook ({target_url}) con token={access_token[:10]}...: {e}")
        if r is not None:
            print("   Response:", r.text)
        return None

# Actualiza un webhook existente, según su id, para que apunte a target_url y quede suscrito a eventos
#Devuelve el JSON completo de respuesta si se actualiza con éxito, o None si falla
def update_webhook(access_token: str, webhook_id: str, target_url: str, topics: list):
    url = f"{MP_API_BASE}/{webhook_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    body = {
        "url": target_url,
        "topics": topics
    }

    try:
        print(f"Actualizando webhook {webhook_id} → nueva URL: {target_url}")
        r = requests.put(url, json=body, headers=headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error actualizando webhook {webhook_id}: {e}")
        if r is not None:
            print("   Response:", r.text)
        return None

#revisa que exista un webhook en el entorno, si es sandbox, no se puede hacer automaticamente (se hace manualmente en mercado pago)
#si es produccion actualiza vía API
def ensure_webhook(access_token: str, ngrok_url: str, topics: list, env_name: str):

    # Sandbox, manualmente en mercado pago
    if access_token.startswith("TEST-"):
        print(f"\nEn {env_name} (Sandbox) la API de Webhooks está deshabilitada.")
        print("Por favor, crea el webhook manualmente desde: Dashboard → Tu App → Webhooks & Notifications.\n")
        return

    # produccion
    base_endpoint = f"{ngrok_url}/webhook/mercadopago/"
    existing = list_webhooks(access_token)

    if existing is None:
        print(f"No se pudo listar webhooks en {env_name}.")
        return

    if len(existing) == 0:
        print(f"No existen webhooks en {env_name}. Creando uno nuevo...")
        nuevo = create_webhook(access_token, base_endpoint, topics)
        if nuevo and nuevo.get("id"):
            print(f"Creado Webhook en {env_name}: id={nuevo.get('id')}, url={nuevo.get('url')}")
        else:
            print(f"Falló la creación del webhook en {env_name}.")
    else:
        w = existing[0]
        wid = w.get("id")
        wurl = w.get("url")
        print(f"Encontrado Webhook en {env_name}: id={wid}, url={wurl}")
        actualizado = update_webhook(access_token, wid, base_endpoint, topics)
        if actualizado and actualizado.get("id"):
            print(f"Actualizado Webhook en {env_name}: id={actualizado.get('id')}, url={actualizado.get('url')}")
        else:
            print(f"Falló la actualización del webhook {wid} en {env_name}.")

#actualiza el campo back_url de los planes en sandbox
def update_plan_back_url(access_token: str, plan_id: str, ngrok_url: str):

    url = f"https://api.mercadopago.com/preapproval_plan/{plan_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    body = {
        "back_url": f"{ngrok_url}/index/pago/exito/"
    }

    try:
        print(f"Intentando actualizar plan {plan_id} en {url}")
        print(f"Usando token: {access_token[:10]}...")
        print(f"Body de la petición: {json.dumps(body, indent=2)}")
        r = requests.put(url, json=body, headers=headers)
        print(f"Respuesta del servidor: {r.status_code}")
        if r.status_code != 200:
            print(f"Contenido de la respuesta: {r.text}")
        else:
            print(f"Plan {plan_id} actualizado (back_url) en Mercado Pago.")
    except Exception as e:
        print(f"Excepción al actualizar plan {plan_id}: {e}")


if __name__ == "__main__":
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("No se pudo obtener la URL de ngrok. Asegúrate de que ngrok esté corriendo en el puerto 4040.")
        exit(1)

    # 1actualizar settings.py
    update_settings(ngrok_url)

    # 2 en sandbox, omite la actualizacion de Webhook (se hace manualmente en mercado pago)
    print("\n=== Actualizando Webhook en SANDBOX ===")
    ensure_webhook(MP_ACCESS_TOKEN_SANDBOX, ngrok_url, WEBHOOK_TOPICS, env_name="SANDBOX")

    # 3 actualizar back_url de los planes en Sandbox
    print("\n=== Actualizando back_url de Planes (Sandbox) ===")
    for pid in PLAN_IDS:
        update_plan_back_url(MP_ACCESS_TOKEN_SANDBOX, pid, ngrok_url)

    print("\nProceso finalizado.")
