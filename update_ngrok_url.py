
import re
import requests
from pathlib import Path

# Ruta a settings.py 
SETTINGS_PATH = Path("Alpatex/settings.py")

# Nombre de la variable en settings.py
NGROK_VAR_NAME = "NGROK_URL"

#Consulta el API local de ngrok para obtener la url
# Devuelve una URL como 'https://abcd1234.ngrok.io' o None si falla
def get_ngrok_url():
    # Verifica si ngrok está corriendo
    try:
        # Realiza una solicitud al API de ngrok
        r = requests.get("http://localhost:4040/api/tunnels")
        # Verifica el estado de la respuesta
        r.raise_for_status()
        # Extrae la URL del túnel HTTPS
        # La respuesta es un JSON
        data = r.json()
        # Busca el túnel HTTPS 
        # data.get("tunnels") es una lista de diccionarios
        # Cada túnel tiene un campo "proto" que indica el protocolo (http o https
        # y un campo "public_url" que es la URL pública del túnel
        for t in data.get("tunnels", []):
            # Verifica si el túnel es HTTPS
            if t.get("proto") == "https":
                # Retorna la URL pública del túnel
                return t.get("public_url")
    # Si ocurre un error al hacer la solicitud o procesar la respuesta
    except Exception as e:
        print("Error obteniendo la URL de ngrok:", e)
    return None

#inserta o reemplaza la línea NGROK_URL = 'ngrok_url' en settings.py
#Actualiza ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS para incluir el dominio de ngrok
def update_settings(ngrok_url: str):
    # Verifica que el archivo settings.py exista
    if not SETTINGS_PATH.exists():
        print(f"No se encontró el archivo {SETTINGS_PATH}")
        return
    
    #guarda el contenido del archivo settings.py
    content = SETTINGS_PATH.read_text(encoding="utf-8")
    
    ngrok_pattern = rf"{NGROK_VAR_NAME}\s*=\s*['\"].*?['\"]"
    nuevo_ngrok = f"{NGROK_VAR_NAME} = '{ngrok_url}'"
    
    #busca en content la línea donde se define la variable de la URL de ngrok con ngrok_pattern
    #y lo reemplaza por nuevo_ngrok 
    if re.search(ngrok_pattern, content):
        content = re.sub(ngrok_pattern, nuevo_ngrok, content)
    else:
        content += f"\n\n# URL pública de ngrok (se actualiza automáticamente)\n{nuevo_ngrok}\n"

    # Extraer el dominio de ngrok (sin el protocolo)
    ngrok_domain = ngrok_url.replace('https://', '').replace('http://', '')
    
    # buscan la lista de hosts permitidos (ALLOWED_HOSTS) en settings.py (content)
    #define la expresión regular para encontrar ALLOWED_HOSTS
    hosts_pattern = r"ALLOWED_HOSTS\s*=\s*\[(.*?)\]"
    # Busca ALLOWED_HOSTS en el contenido
    hosts_match = re.search(hosts_pattern, content, re.DOTALL)
    
    # Si ALLOWED_HOSTS ya existe, actualiza o agrega el dominio de ngrok y hosts locales
    if hosts_match:
        # Extrae la lista actual de hosts
        # hosts_match.group(1) contiene el contenido entre los corchetes de ALLOWED_HOSTS
        current_hosts = hosts_match.group(1)
        #limpiar la lista actual de hosts, eliminando espacios y comillas
        hosts_set = {h.strip().strip("'\"") for h in current_hosts.split(',') if h.strip()}
        # Agregar el nuevo dominio y los hosts locales si no existen
        hosts_set.update([ngrok_domain, 'localhost', '127.0.0.1'])
        #ordena el conjunto de hosts alfabéticamente y los convierte en una lista
        hosts_list = sorted(list(hosts_set))
        #crea un nuevo contenido para ALLOWED_HOSTS, los pone dentro de corchetes y los convierte a string
        new_hosts = f"ALLOWED_HOSTS = [{', '.join(repr(h) for h in hosts_list)}]"
        #Reemplaza la línea original de ALLOWED_HOSTS en el contenido por la nueva línea generada
        content = re.sub(hosts_pattern, new_hosts, content)
    else:
        # agrega la configuración de ALLOWED_HOSTS si no existe en el archivo
        debug_pattern = r"(DEBUG\s*=\s*True)"
        new_hosts = f"\\1\n\nALLOWED_HOSTS = ['{ngrok_domain}', 'localhost', '127.0.0.1']"
        content = re.sub(debug_pattern, new_hosts, content)

    #Permite localizar y extraer la lista de orígenes confiables para CSRF en  settings.py
    csrf_pattern = r"CSRF_TRUSTED_ORIGINS\s*=\s*\[(.*?)\]"
    csrf_match = re.search(csrf_pattern, content, re.DOTALL)
    
    if csrf_match:
        # Extrae la lista actual de orígenes confiables
        # csrf_match.group(1) contiene el contenido entre los corchetes de CSRF_TRUSTED_ORIGINS
        current_origins = csrf_match.group(1)
        # limpiar la lista actual de orígenes, eliminando espacios y comillas
        origins_set = {o.strip().strip("'\"") for o in current_origins.split(',') if o.strip()}
        # Agregar el nuevo origen de ngrok si no existe
        origins_set.add(ngrok_url)
        # Convertir de vuelta a una lista ordenada
        origins_list = sorted(list(origins_set))
        # Crear una nueva línea para CSRF_TRUSTED_ORIGINS
        # Convertir la lista a string, asegurando que cada origen esté entre comillas
        new_csrf = f"CSRF_TRUSTED_ORIGINS = [{', '.join(repr(o) for o in origins_list)}]"
        # Reemplazar la línea original de CSRF_TRUSTED_ORIGINS en el contenido por la nueva línea generada
        content = re.sub(csrf_pattern, new_csrf, content)
    else:
        # Si no existe CSRF_TRUSTED_ORIGINS, se agrega después de ALLOWED_HOSTS
        hosts_pattern = r"(ALLOWED_HOSTS\s*=\s*\[.*?\])"
        new_csrf = f"\\1\n\nCSRF_TRUSTED_ORIGINS = ['{ngrok_url}']"
        content = re.sub(hosts_pattern, new_csrf, content, flags=re.DOTALL)
    # Escribe el contenido actualizado de settings.py
    SETTINGS_PATH.write_text(content, encoding="utf-8")
    print(f"settings.py actualizado:")
    print(f"- {NGROK_VAR_NAME} = '{ngrok_url}'")
    print(f"- ALLOWED_HOSTS actualizado para incluir '{ngrok_domain}'")
    print(f"- CSRF_TRUSTED_ORIGINS actualizado para incluir '{ngrok_url}'")

#flujo principal del script
if __name__ == "__main__":
    #extrae la URL de ngrok
    ngrok_url = get_ngrok_url()
    # Si no se pudo obtener la URL de ngrok, muestra un mensaje de error y termina
    if not ngrok_url:
        print("No se pudo obtener la URL de ngrok. Asegúrate de que ngrok esté corriendo en el puerto")
        exit(1)

    #si  se obtuvo la URL de ngrok, actualiza settings.py
    update_settings(ngrok_url)

    print("\nProceso finalizado.")
