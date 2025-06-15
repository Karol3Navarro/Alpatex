import os
from django.conf import settings

# Credenciales de Mercado Pago Sandbox (MODO PRUEBA)
MERCADOPAGO_ACCESS_TOKEN = "APP_USR-8742947522442677-060223-396c1153906822a73b663c752f0baf33-2461175817"
MERCADOPAGO_PUBLIC_KEY = "APP_USR-92c6bcfe-4853-4768-a8e7-e4015fc9219e"

# Credenciales de Mercado Pago Producción (MODO REAL)
MERCADOPAGO_ACCESS_TOKEN_PROD = "APP_USR-7429934597752386-052722-02335e93139d8f32b0e2544fb0a4d780-2464461320"
MERCADOPAGO_PUBLIC_KEY_PROD = "APP_USR-bbbfdb4d-55c2-4d7b-8ae4-d1ec450749a5"

# toma la url de ngrok y la usa para construir o actualizar las url de webhook, exito y rechzo
def get_base_url():
    if hasattr(settings, 'NGROK_URL'):
        return settings.NGROK_URL
    return settings.BASE_URL

# URLs para Sandbox
MERCADOPAGO_WEBHOOK_URL = f"{get_base_url()}/index/webhook/mercadopago/"
MERCADOPAGO_SUCCESS_URL = f"{get_base_url()}/index/pago/exito/"
MERCADOPAGO_FAILURE_URL = f"{get_base_url()}/index/pago/fallo/"
MERCADOPAGO_PENDING_URL = f"{get_base_url()}/index/pago/fallo/"

# Configuración de suscripciones
SUBSCRIPTION_FREQUENCY = 30  # días
SUBSCRIPTION_FREQUENCY_TYPE = "days" 