# admin_alpatex/services.py

import mercadopago
import requests
from django.utils import timezone
from datetime import timedelta
from .models import SuscripcionMercadoPago
from .mercadopago_config import (
    MERCADOPAGO_ACCESS_TOKEN,
    MERCADOPAGO_WEBHOOK_URL,
    MERCADOPAGO_SUCCESS_URL,
    MERCADOPAGO_FAILURE_URL,
    MERCADOPAGO_PENDING_URL,
    SUBSCRIPTION_FREQUENCY
)

class MercadoPagoService:
    def __init__(self):
        # Inicializar el SDK con el Access Token de SANDBOX
        self.sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)

    def crear_suscripcion(self, perfil, membresia, token_tarjeta):
        """
        Crea una suscripción en Mercado Pago (Sandbox).
        Devuelve el diccionario de respuesta de la API para que contenga init_point / sandbox_init_point.
        Además, crea un registro en el modelo SuscripcionMercadoPago.
        """
        try:
            # Validaciones básicas
            if not token_tarjeta or not isinstance(token_tarjeta, str):
                raise Exception("No se recibió un token de tarjeta válido")

            # Construir los datos de la suscripción
            subscription_data = {
                "preapproval_plan_id": membresia.plan_id,
                "reason": membresia.nombre,
                "payer_email": perfil.user.email,
                "card_token_id": token_tarjeta,
                "notification_url": MERCADOPAGO_WEBHOOK_URL,
                "back_url": MERCADOPAGO_SUCCESS_URL,
                "failure_url": MERCADOPAGO_FAILURE_URL,
                "pending_url": MERCADOPAGO_PENDING_URL
            }

            # Llamada a la API de Mercado Pago
            response = self.sdk.subscription().create(subscription_data)

            # Si el estado es 201, la suscripción se creó correctamente
            if response["status"] == 201:
                api_response = response["response"]

                # Guardar en la bd
                SuscripcionMercadoPago.objects.create(
                    perfil=perfil,
                    membresia=membresia,
                    subscription_id=api_response["id"],
                    token_tarjeta=token_tarjeta,
                    fecha_inicio=timezone.now(),
                    fecha_fin=timezone.now() + timedelta(days=SUBSCRIPTION_FREQUENCY)
                )

                # Devolvemos todo el dict que vino de Mercado Pago
                return api_response

            else:
                # Si no fue 201, levantamos excepción para que el controlador lo maneje
                raise Exception(f"Error al crear suscripción: {response['response']}")

        except Exception as e:
            # Lanzamos la excepción para que el caller (la vista) la capture
            raise Exception(f"Error en crear_suscripcion: {str(e)}")

    def cancelar_suscripcion(self, suscripcion):
        """
        Cancela una suscripción en Mercado Pago y actualiza el estado en el modelo.
        """
        try:
            url = f"https://api.mercadopago.com/preapproval/{suscripcion.subscription_id}"
            headers = {
                "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            data = {
                "status": "cancelled"
            }
            response = requests.put(url, headers=headers, json=data)
            if response.status_code == 200:
                suscripcion.estado = "cancelled"
                suscripcion.fecha_cancelacion = timezone.now()
                suscripcion.save()
                return True
            else:
                raise Exception(f"Error al cancelar suscripción: {response.text}")

        except Exception as e:
            raise Exception(f"Error en cancelar_suscripcion: {str(e)}")

    def procesar_webhook(self, data):
        """
        Procesa las notificaciones webhook de Mercado Pago.
        Actualiza el registro de SuscripcionMercadoPago cuando llegue un payment o una cancelación.
        """
        try:
            # PAgo
            if data.get("type") == "payment":
                payment_id = data["data"]["id"]
                payment_info = self.sdk.payment().get(payment_id)

                if payment_info["status"] == 200:
                    payment_data = payment_info["response"]
                    subscription_id = payment_data.get("subscription_id")

                    if subscription_id:
                        suscripcion = SuscripcionMercadoPago.objects.get(subscription_id=subscription_id)
                        perfil = suscripcion.perfil

                        if payment_data["status"] == "approved":
                            suscripcion.ultimo_pago = timezone.now()
                            suscripcion.actualizar_proximo_pago()
                            suscripcion.save()

                            # asigna la membresia
                            perfil.membresia = suscripcion.membresia
                            perfil.save()

                        elif payment_data["status"] == "rejected":
                            suscripcion.estado = "expired"
                            suscripcion.save()

                            # quita membresia
                            perfil.membresia = None
                            perfil.save()

            # cancelacion de suscripcion
            elif data.get("type") == "subscription":
                subscription_id = data["data"]["id"]
                # Obtiene el estado de la suscripción desde la API de MercadoPago
                subscription_info = self.sdk.subscription().get(subscription_id)
                if subscription_info["status"] == 200:
                    subscription_data = subscription_info["response"]
                    status = subscription_data.get("status")
                    if status == "cancelled":
                        suscripcion = SuscripcionMercadoPago.objects.get(subscription_id=subscription_id)
                        perfil = suscripcion.perfil
                        suscripcion.estado = "cancelled"
                        suscripcion.fecha_cancelacion = timezone.now()
                        suscripcion.save()

                        # quita membresia
                        perfil.membresia = None
                        perfil.save()

            return True

        except SuscripcionMercadoPago.DoesNotExist:
            raise Exception(f"Suscripción con ID {subscription_id} no encontrada")
        except Exception as e:
            raise Exception(f"Error en procesar_webhook: {str(e)}")
