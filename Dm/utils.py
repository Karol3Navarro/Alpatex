from .models import CanalMensaje

def contar_mensajes_no_leidos(user):
    if user.is_authenticated:
        return CanalMensaje.objects.filter(
            canal__canalusuario__usuario=user
        ).exclude(leido_por=user).exclude(usuario=user).count()
    return 0