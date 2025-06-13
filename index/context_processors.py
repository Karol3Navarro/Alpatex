from Dm.models import Canal, CanalMensaje  # importa los modelos que uses
from django.db.models import Q

def mensajes_no_leidos(request):
    if request.user.is_authenticated:
        canales = Canal.objects.filter(canalusuario__usuario=request.user)
        no_leidos = 0
        for canal in canales:
            no_leidos += canal.canalmensaje_set.exclude(leido_por=request.user).exclude(usuario=request.user).count()
        return {
            'mensajes_no_leidos': no_leidos
        }
    return {
        'mensajes_no_leidos': 0
    }
