from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import CanalMensaje, CanalUsuario, Canal
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .forms import FormMensajes
from django.views.generic.edit import FormMixin
from django.views.generic import View
from index.models import Producto
from django.urls import reverse
# Create your views here.
def home_index(request):
	# Aquí puedes pasar el contexto que necesites para tu página de inicio
	return render(request, 'index/index.html')

class Inbox(View):
	def get(self, request):
		inbox = Canal.objects.filter(canalusuario__usuario=request.user)

		canal_id = request.GET.get('canal_id')
		canal = None

		if canal_id:
			try:
				canal = Canal.objects.get(id=canal_id)
			except Canal.DoesNotExist:
				canal = None  # O podrías manejar con Http404

		context = {
			"inbox": inbox,
			"canal": canal,
			"form": FormMensajes()
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

		if getattr(self, 'enviar_mensaje', False):
			canal = self.get_object()
			usuario = self.request.user

			url_producto = self.request.build_absolute_uri(
				reverse('ver_producto', kwargs={'id_producto': self.producto.id_producto})
			)

			texto_mensaje = f""" 
				¡Hola! Estoy interesado en tu producto: {self.producto.nombre}.<br>
				<img src="{self.request.build_absolute_uri(self.producto.imagen.url)}" alt="{self.producto.nombre}" style="max-width: 150px; height: auto; margin-top: 10px;" />. <br>
				<a href="{url_producto}" class="btn btn-primary" style="margin-top: 10px; display: inline-block;">Ver Producto</a>
			"""

			# Evitar duplicados: revisamos si ya existe este mensaje del usuario
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

		context['inbox'] = Canal.objects.filter(canalusuario__usuario=self.request.user)
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