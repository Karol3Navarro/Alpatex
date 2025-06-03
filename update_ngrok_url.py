import os
import json
import re
import requests
from pathlib import Path


# Token de prueba (Sandbox) 
MP_ACCESS_TOKEN_SANDBOX = "TEST-7429934597752386-052722-2b3af6cbfe000d172d6b847019a36d3d-2464461320"

# Token de Producción 
MP_ACCESS_TOKEN_PROD = "APP_USR-7429934597752386-052722-02335e93139d8f32b0e2544fb0a4d780-2464461320"

# ID planes 
PLAN_IDS = [
    "2c938084970fb5df01972e615a200bcb",  # Plan Oro
    "2c93808497271d1901972e62675a0211",  # Plan Plata
]

# Lista de eventos para recibir en el Webhook.
WEBHOOK_TOPICS = ["payment", "preapproval"]

# Ruta a settings.py
SETTINGS_PATH = Path("Alpatex/settings.py")

# Nombre de la variable definida en settings.py
NGROK_VAR_NAME = "NGROK_URL"


# OBTENER URL PÚBLICA DE NGROK

def get_ngrok_url():
    """
    Consulta el API local de ngrok para obtener el túnel HTTPS.
    Devuelve url generica como 'https://abcd1234.ngrok.io' o None si falla.
    """
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


#ACTUALIZAR settings.py

def update_settings(ngrok_url: str):
    """
    Inserta o reemplaza la línea NGROK_URL = 'ngrok_url' en settings.py.
    """
    if not SETTINGS_PATH.exists():
        print(f"No se encontró el archivo {SETTINGS_PATH}")
        return

    content = SETTINGS_PATH.read_text(encoding="utf-8")

    pattern = rf"{NGROK_VAR_NAME}\s*=\s*['\"].*?['\"]"
    nuevo = f"{NGROK_VAR_NAME} = '{ngrok_url}'"

    if re.search(pattern, content):

        content = re.sub(pattern, nuevo, content)
    else:

        content += f"\n\n# URL pública de ngrok (se actualiza automáticamente)\n{nuevo}\n"

    SETTINGS_PATH.write_text(content, encoding="utf-8")
    print(f"settings.py actualizado: {NGROK_VAR_NAME} = '{ngrok_url}'")




MP_API_BASE = "https://api.mercadopago.com/v1/webhooks"


def list_webhooks(access_token: str):
    """
    Lista todos los webhooks del entorno
    Retorna la lista de objetos o None si falla.
    """
    url = MP_API_BASE
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        payload = r.json()
        return payload.get("data", [])
    except Exception as e:
        print(f"Error listando webhooks (token={access_token[:10]}...): {e}")
        return None


def create_webhook(access_token: str, target_url: str, topics: list):
    """
    Crea un nuevo webhook apuntando a target_url, suscrito a los eventos 
    Devuelve el JSON de respuesta o None si falla.
    """
    url = MP_API_BASE
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    body = {
        "url": target_url,
        "enabled_events": topics
    }
    try:
        r = requests.post(url, json=body, headers=headers)
        r.raise_for_status()
        return r.json().get("data", {})
    except Exception as e:
        print(f"Error creando webhook ({target_url}) con token={access_token[:10]}...: {e}")
        if r is not None:
            print("   Response:", r.text)
        return None


def update_webhook(access_token: str, webhook_id: str, target_url: str, topics: list):
    """
    Actualiza un webhook existente (según su ID) para que apunte a target_url
    y quede suscrito a eventos
    Devuelve el JSON de respuesta o None si falla.
    """
    url = f"{MP_API_BASE}/{webhook_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    body = {
        "url": target_url,
        "enabled_events": topics
    }
    try:
        r = requests.put(url, json=body, headers=headers)
        r.raise_for_status()
        return r.json().get("data", {})
    except Exception as e:
        print(f"Error actualizando webhook {webhook_id}: {e}")
        if r is not None:
            print("   Response:", r.text)
        return None


def ensure_webhook(access_token: str, ngrok_url: str, topics: list, env_name: str):
    """
    Se encarga de que exista un webhook en este entorno (Sandbox o Prod).
    - Si la lista es vacía, crea uno nuevo apuntando a ngrok_url + '/webhook/mercadopago/'.
    - Si ya hay al menos uno, toma el primero y lo actualiza.
    """
    base_endpoint = f"{ngrok_url}/webhook/mercadopago/"
    existing = list_webhooks(access_token)
    if existing is None:
        print(f"No se pudo listar webhooks en {env_name}.")
        return

    if len(existing) == 0:
        print(f"No existen webhooks en {env_name}. Creando uno nuevo...")
        nuevo = create_webhook(access_token, base_endpoint, topics)
        if nuevo:
            print(f"Creado Webhook en {env_name}: id={nuevo.get('id')}, url={nuevo.get('url')}")
        else:
            print(f"Falló la creación del webhook en {env_name}.")
    else:
        # Toma el primero que encuentra y lo actualiza
        w = existing[0]
        wid = w.get("id")
        wurl = w.get("url")
        print(f"Encontrado Webhook en {env_name}: id={wid}, url={wurl}")
        actualizado = update_webhook(access_token, wid, base_endpoint, topics)
        if actualizado:
            print(f"Actualizado Webhook en {env_name}: id={actualizado.get('id')}, url={actualizado.get('url')}")
        else:
            print(f"Falló la actualización del webhook {wid} en {env_name}.")


# ACTUALIZAR back_url DE PLANES 

def update_plan_back_url(access_token: str, plan_id: str, ngrok_url: str):
    """
    Para cada plan_id, hace un PUT a /preapproval_plan/{plan_id} y actualiza el campo back_url
    apuntando a ngrok_url/index/pago/exito/.
    Esto es independiente del Webhook
    """
    url = f"https://api.mercadopago.com/preapproval_plan/{plan_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    body = {
        "back_url": f"{ngrok_url}/index/pago/exito/"
    }
    try:
        r = requests.put(url, json=body, headers=headers)
        if r.status_code == 200:
            print(f"Plan {plan_id} actualizado (back_url) en Mercado Pago.")
        else:
            print(f"Error actualizando Plan {plan_id}: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Excepción al actualizar plan {plan_id}: {e}")


# MAIN 

if __name__ == "__main__":
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("No se pudo obtener la URL de ngrok. Asegúrate de que ngrok esté corriendo en el puerto 4040.")
        exit(1)

    # 1) Actualizo settings.py
    update_settings(ngrok_url)

    # 2) En Sandbox, crear/actualizar el Webhook
    print("\n=== Actualizando Webhook en SANDBOX ===")
    ensure_webhook(MP_ACCESS_TOKEN_SANDBOX, ngrok_url, WEBHOOK_TOPICS, env_name="SANDBOX")

    # 3) En Producción, crear/actualizar el Webhook
    print("\n=== Actualizando Webhook en PRODUCCIÓN ===")
    ensure_webhook(MP_ACCESS_TOKEN_PROD, ngrok_url, WEBHOOK_TOPICS, env_name="PRODUCCIÓN")

    # 4) actualiza los back_url de los planes en Sandbox
  
    print("\n=== Actualizando back_url de Planes (Sandbox) ===")
    for pid in PLAN_IDS:
        update_plan_back_url(MP_ACCESS_TOKEN_SANDBOX, pid, ngrok_url)

    print("\nProceso finalizado.")
