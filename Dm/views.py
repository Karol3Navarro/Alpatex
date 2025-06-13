from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import CanalMensaje, CanalUsuario, Canal
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .forms import FormMensajes
from django.views.generic.edit import FormMixin
from django.views.generic import View
from index.models import Producto, CalificacionCliente, CalificacionVendedor, ReporteVendedor
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, time
from .models import ConfirmacionEntrega
from django.utils.timezone import localtime
from datetime import timedelta
from django.utils.timezone import localtime, make_aware, get_current_timezone, now
from .utils import contar_mensajes_no_leidos

# Create your views here.
def home_index(request):
	# Aquí puedes pasar el contexto que necesites para tu página de inicio
	return render(request, 'index/index.html')

class Inbox(View):
	def get(self, request):
		inbox = Canal.objects.filter(canalusuario__usuario=request.user)
		
		canal_id = request.GET.get('canal_id')
		canal = None
		producto_relacionado = None
		es_duenio_producto = False
		confirmacion = None
		mostrar_botones = False

		calificacion_cliente = False
		cliente = None

		mostrar_boton_entrega = False 
		if canal_id:
			try:
				canal = Canal.objects.get(id=canal_id)

				# ✅ Marcar como leídos
				mensajes_sin_leer = canal.canalmensaje_set.exclude(leido_por=request.user).exclude(usuario=request.user)
				if mensajes_sin_leer.exists():
					for mensaje in mensajes_sin_leer:
						mensaje.leido_por.add(request.user)
					# 🔄 Redirigir para actualizar el contador de base.html
					return redirect(f"{request.path}?canal_id={canal.id}")

				# 🔔 Marcar como leídos los mensajes de este canal que aún no lo están
				mensajes_sin_leer = canal.canalmensaje_set.exclude(leido_por=request.user).exclude(usuario=request.user)
				for mensaje in mensajes_sin_leer:
					mensaje.leido_por.add(request.user)

				# 🔍 Buscamos el último mensaje con producto
				mensaje_con_producto = canal.canalmensaje_set.filter(producto__isnull=False).order_by('-tiempo').first()
				if mensaje_con_producto:
					producto_relacionado = mensaje_con_producto.producto
					es_duenio_producto = (producto_relacionado.usuario == request.user)

					if producto_relacionado:
						# Verificamos si ya existe una confirmación de entrega
						confirmacion = ConfirmacionEntrega.objects.filter(canal=canal, producto=producto_relacionado).first()
						if not confirmacion:  # Si no hay confirmación, mostramos el botón
							mostrar_boton_entrega = True

					cliente = canal.canalusuario_set.exclude(usuario=producto_relacionado.usuario).first()
					if cliente:
						cliente = cliente.usuario

				confirmacion = ConfirmacionEntrega.objects.filter(canal=canal).order_by('-creado_en').first()
				
				if confirmacion:
					# Combinar fecha y hora en naive datetime
					fecha_hora_naive = datetime.combine(confirmacion.fecha, confirmacion.hora)
					
					# Forzar zona horaria activa de Django
					zona_local = get_current_timezone()
					fecha_hora = make_aware(fecha_hora_naive, timezone=zona_local)

					# Obtener el tiempo actual en zona local
					ahora = localtime(now())

					if ahora >= fecha_hora and not es_duenio_producto:
						mostrar_botones = True
					else:
						mostrar_botones = False

					calificacion_vendedor = CalificacionVendedor.objects.filter(producto=producto_relacionado, comprador=request.user).exists()
					reporte_cliente = ReporteVendedor.objects.filter(producto=producto_relacionado, comprador=request.user).exists()
					
					if calificacion_vendedor or reporte_cliente:
						mostrar_botones = False

					if producto_relacionado and es_duenio_producto:
						confirmacion = ConfirmacionEntrega.objects.filter(
							canal=canal, producto=producto_relacionado, confirmado=True
						).order_by('-creado_en').first()

						if confirmacion:
							ya_calificado = CalificacionCliente.objects.filter(
								producto=producto_relacionado,
								vendedor=request.user
							).exists()
							calificacion_cliente = not ya_calificado

			except Canal.DoesNotExist:
				canal = None  # O podrías manejar con Http404

		# ✅ Ahora sí contar los mensajes no leídos después de marcar
		mensajes_no_leidos = contar_mensajes_no_leidos(request.user)

		context = {
			"inbox": inbox,
			"canal": canal,
			"form": FormMensajes(),
			"mostrar_boton_entrega": mostrar_boton_entrega,
			"producto_relacionado": producto_relacionado,
			"es_duenio_producto": es_duenio_producto,
			"confirmacion": confirmacion,
			"mostrar_botones": mostrar_botones,
			"cliente":cliente,
			"calificacion_cliente": calificacion_cliente,
			"mensajes_no_leidos": mensajes_no_leidos,
		}

		return render(request, 'index/inbox.html', context)

	def post(self, request):
		canal_id = request.GET.get('canal_id')
		try:
			canal = Canal.objects.get(id=canal_id)
		except Canal.DoesNotExist:
			return redirect("nombre_de_url_inbox")  # fallback si canal no existe

		if request.user.is_authenticated and canal:
			form = FormMensajes(request.POST)
			if form.is_valid():
				mensaje = form.cleaned_data['mensaje']
				CanalMensaje.objects.create(canal=canal, usuario=request.user, texto=mensaje)

				# ✅ REDIRECCIÓN para evitar duplicación al recargar
				return redirect(f"{request.path}?canal_id={canal.id}")

		# Si no es válido o algo falla, renderizamos normalmente
		inbox = Canal.objects.filter(canalusuario__usuario=request.user)
		context = {
			"inbox": inbox,
			"canal": canal,
			"form": form
		}
		return render(request, 'index/inbox.html', context)


class CanalFormMixin(FormMixin):
	form_class =FormMensajes
	#success_url = "./"

	def get_success_url(self):
		return self.request.path

	def post(self, request, *args, **kwargs):

		if not request.user.is_authenticated:
			raise PermissionDenied

		form = self.get_form()
		if form.is_valid():
			canal = self.get_object()
			usuario = self.request.user 
			mensaje = form.cleaned_data.get("mensaje")
			canal_obj = CanalMensaje.objects.create(canal=canal, usuario=usuario, texto=mensaje)
			
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':

				return JsonResponse({

			 		'mensaje':canal_obj.texto,
			 		'username':canal_obj.usuario.username
			 	}, status=201)

			return super().form_valid(form)

		else:
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':

				return JsonResponse({"Error":form.errors}, status=400)

			return super().form_invalid(form)

class CanalDetailView(LoginRequiredMixin, CanalFormMixin, DetailView):
	template_name= 'index/inbox.html'
	queryset = Canal.objects.all()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		obj = context['object']
		context['si_canal_mienbro'] = self.request.user in obj.usuarios.all()
		context['inbox'] = Canal.objects.filter(canalusuario__usuario=self.request.user)
		context['form'] = FormMensajes()
		return context
	
	 

class DetailMs(LoginRequiredMixin, CanalFormMixin, DetailView):
	template_name = 'index/inbox.html'

	def get_object(self, *args, **kwargs):
		username = self.kwargs.get("username")
		mi_username = self.request.user.username
		self.enviar_mensaje = False  # bandera

		canal, _ = Canal.objects.obtener_o_crear_canal_ms(mi_username, username)

		producto_id = self.request.GET.get("producto_id")
		if producto_id:
			self.producto = get_object_or_404(Producto, id_producto=producto_id)
			self.enviar_mensaje = True

		return canal

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		canal = self.get_object()
		usuario = self.request.user

		# MENSAJE AUTOMÁTICO ADMINISTRADOR
		if usuario.is_staff or usuario.is_superuser:
			texto_mensaje = (
				"Hola, soy el Administrador de Alpatex. <br>"
				"Veo que tienes reportes en tu perfil. Según las políticas de la plataforma, debes:<br>"
				"1️⃣ Coordinar otra fecha y lugar para la nueva entrega del producto.<br>"
				"2️⃣ Si tienes más de 3 reportes, nos veremos en la obligación de eliminar tu perfil.<br>"
				"3️⃣ Contactar soporte si crees que el reporte fue un error.<br>"
				"Gracias por tu comprensión."
			)

			ya_enviado = CanalMensaje.objects.filter(
				canal=canal,
				usuario=usuario,
				texto=texto_mensaje
			).exists()

			if not ya_enviado:
				CanalMensaje.objects.create(
					canal=canal,
					usuario=usuario,
					texto=texto_mensaje
				)

		# MENSAJE DE INTERÉS POR PRODUCTO
		elif getattr(self, 'enviar_mensaje', False):
			url_producto = self.request.build_absolute_uri(
				reverse('ver_producto', kwargs={'id_producto': self.producto.id_producto})
			)

			texto_mensaje = f""" 
				¡Hola! Estoy interesado en tu producto: {self.producto.nombre}.<br>
				<img src="{self.request.build_absolute_uri(self.producto.imagen.url)}" alt="{self.producto.nombre}" style="max-width: 150px; height: auto; margin-top: 10px;" /> <br>
				<a href="{url_producto}" class="btn btn-primary" style="margin-top: 10px; display: inline-block;">Ver Producto</a>
			"""

			ya_enviado = CanalMensaje.objects.filter(
				canal=canal,
				usuario=usuario,
				texto=texto_mensaje
			).exists()

			if not ya_enviado:
				CanalMensaje.objects.create(
					canal=canal,
					usuario=usuario,
					texto=texto_mensaje,
					producto=self.producto
				)

		context['inbox'] = Canal.objects.filter(canalusuario__usuario=usuario)
		context['form'] = FormMensajes()
		return context

def mensajes_privados(request, username, *args, **kwargs):
	if not request.user.is_authenticated:
		return HttpResponse("Prohibido")

	mi_username = request.user.username

	canal, created =Canal.objects.obtener_o_crear_canal_ms(mi_username, username)
	if created:
		print("Si, fue creado")
	
	Usuarios_Canal = canal.canalusuario_set.all().values("usuario__username")
	print(Usuarios_Canal)
	mensaje_canal = canal.canalmensaje_set.all().order_by('tiempo')
	print(mensaje_canal.values("texto"))

		
	return HttpResponse(f"Nuestro Id del Canal - {canal.id}")