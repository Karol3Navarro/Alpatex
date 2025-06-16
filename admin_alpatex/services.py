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
    
    #Inicializa el SDK de Mercado Pago con el Access Token de prueba
    def __init__(self):
        self.sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)

    #Crea una suscripción automática de pago recurrente
    def crear_suscripcion(self, perfil, membresia, token_tarjeta):
        """
        Crea una suscripción en Mercado Pago (Sandbox).
        Devuelve la respuesta de la API de mercado pago 
        Crea un registro en la tabla  SuscripcionMercadoPago.
        """
        try:
            # Valida que el token de tarjeta sea válido, previene errores antes de llamar a la api
            # revisa que no este vacio y sea una cadena
            #La validación real del token de tarjeta la hace Mercado Pago cuando intentas crear un pago
            if not token_tarjeta or not isinstance(token_tarjeta, str):
                raise Exception("No se recibió un token de tarjeta válido")

            # Construir los datos de la suscripción
            subscription_data = {
                "preapproval_plan_id": membresia.plan_id,
                "reason": membresia.nombre,
                "payer_email": perfil.user.email,
                "card_token_id": token_tarjeta, #generado por el frontend a traves de la SDK de Mercado Pago
                "notification_url": MERCADOPAGO_WEBHOOK_URL,
                "back_url": MERCADOPAGO_SUCCESS_URL,
                "failure_url": MERCADOPAGO_FAILURE_URL,
                "pending_url": MERCADOPAGO_PENDING_URL
            }

            # Llamada a la API de Mercado Pago para crear la suscripción
            response = self.sdk.subscription().create(subscription_data)

            # Si el estado es 201, la suscripción se creó correctamente
            if response["status"] == 201:
                api_response = response["response"]

                # Guardar en la bd en la tabla  SuscripcionMercadoPago
                SuscripcionMercadoPago.objects.create(
                    perfil=perfil,
                    membresia=membresia,
                    subscription_id=api_response["id"],
                    token_tarjeta=token_tarjeta,
                    fecha_inicio=timezone.now(),
                    fecha_fin=timezone.now() + timedelta(days=SUBSCRIPTION_FREQUENCY)
                )

                # Devuelve la respuesta de la API de Mercado Pago
                return api_response
        #manejo de excepciones
            else:
                # Si la respuesta no es 201, lanza una excepción con el mensaje de error
                raise Exception(f"Error al crear suscripción: {response['response']}")
        except Exception as e:
            raise Exception(f"Error en crear_suscripcion: {str(e)}")

    #Cancela una suscripción desde el backend y actualiza la base de datos
    #toma como parametro suscripcion, que es un objeto de la clase SuscripcionMercadoPago
    def cancelar_suscripcion(self, suscripcion):
        try:
            #Hace una petición PUT a la API de Mercado Pago para cancelar
            #usa la subscription_id de la suscripción
            url = f"https://api.mercadopago.com/preapproval/{suscripcion.subscription_id}"
            
            # Configura los headers y el cuerpo de la solicitud
            headers = {
                "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            data = {
                "status": "cancelled"
            }
            # Realiza la solicitud PUT para cancelar la suscripción
            # Si la respuesta es exitosa, actualiza el estado de la suscripción en la bd
            response = requests.put(url, headers=headers, json=data)
            if response.status_code == 200:
                suscripcion.estado = "cancelled"
                suscripcion.fecha_cancelacion = timezone.now()
                suscripcion.save()
                return True
        #manejo de excepciones
            else:
                raise Exception(f"Error al cancelar suscripción: {response.text}")
        except Exception as e:
            raise Exception(f"Error en cancelar_suscripcion: {str(e)}")

    #Procesa las notificaciones automáticas que envía Mercado Pago al webhook
    #parametro "data" es el diccionario recibido en el webhook.
    #Puede ser de tipo payment o tipo subscription
    #Si es de tipo payment, busca la suscripción por subscription_id y actualiza el estado del pago
    #Si es de tipo subscription, busca la suscripción por subscription_id y actualiza el estado de la suscripción
    def procesar_webhook(self, data):
        try:
            # Obtiene el payment_id y consulta los datos del pago
            if data.get("type") == "payment":
                payment_id = data["data"]["id"]
                payment_info = self.sdk.payment().get(payment_id)

                #Busca la suscripción por subscription_id en la tabla SuscripcionMercadoPago
                if payment_info["status"] == 200:
                    payment_data = payment_info["response"]
                    subscription_id = payment_data.get("subscription_id")

                    # Si se encuentra el subscription_id, busca la suscripción en la base de datos
                    # y actualiza el estado del pago
                    if subscription_id:
                        suscripcion = SuscripcionMercadoPago.objects.get(subscription_id=subscription_id)
                        perfil = suscripcion.perfil
                        
                        #Si el pago es aprobado, actualiza la fecha de pago y la fecha de próximo pago y asocia la membresia al perfil
                        if payment_data["status"] == "approved":
                            suscripcion.ultimo_pago = timezone.now()
                            suscripcion.actualizar_proximo_pago()
                            suscripcion.save()

                            # asigna la membresia
                            perfil.membresia = suscripcion.membresia
                            perfil.save()
                        
                        #si el pago es rechazado, actualiza el estado de la suscripción a "expired" y quita la membresía del perfil
                        elif payment_data["status"] == "rejected":
                            suscripcion.estado = "expired"
                            suscripcion.save()

                            # quita membresia
                            perfil.membresia = None
                            perfil.save()

            #Verifica si la suscripción fue cancelada (status == "cancelled")
            elif data.get("type") == "subscription":
                # Obtiene el subscription_id del diccionario data
                subscription_id = data["data"]["id"]
                # Obtiene el estado de la suscripción desde la API de MercadoPago
                subscription_info = self.sdk.subscription().get(subscription_id)
                # Si la respuesta es exitosa, actualiza el estado de la suscripción en la base de datos
                if subscription_info["status"] == 200:
                    subscription_data = subscription_info["response"]
                    status = subscription_data.get("status")
                    #Marca la suscripción como cancelada en la bd y quita la membresía del perfil
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
        #manejo de excepciones
        except SuscripcionMercadoPago.DoesNotExist:
            raise Exception(f"Suscripción con ID {subscription_id} no encontrada")
        except Exception as e:
            raise Exception(f"Error en procesar_webhook: {str(e)}")
