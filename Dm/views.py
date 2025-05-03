from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect
from .models import CanalMensaje, CanalUsuario, Canal
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .forms import FormMensajes
from django.views.generic.edit import FormMixin
from django.views.generic import View

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
		canal, _ =Canal.objects.obtener_o_crear_canal_ms(mi_username, username)

		if username == mi_username:
			mi_canal, _ = Canal.objects.obtener_o_crear_canal_usuario_actual(self.request.user)
			return mi_canal

		if canal == None:
			raise Http404

		return canal
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
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