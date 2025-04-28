from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from index.models import Producto, Perfil
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import openpyxl
from django.http import HttpResponse
from datetime import datetime


def dashboard(request):
    return render(request, 'admin_alpatex/home.html')


@staff_member_required
def gestionar_productos(request):
    productos_pendientes = Producto.objects.filter(estado_revision='Pendiente')

    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        accion = request.POST.get('accion')
        print(f"Producto ID recibido: {producto_id}, Acción: {accion}")  # Opcional para debug
        producto = get_object_or_404(Producto, id_producto=producto_id)

        if accion == 'aceptar':
            producto.estado_revision = 'Aceptado'
            producto.motivo_rechazo = ''
        elif accion == 'rechazar':
            producto.estado_revision = 'Rechazado'
            producto.motivo_rechazo = request.POST.get('motivo', '').strip()

        producto.save()
        messages.success(request, f"Producto {accion} correctamente.")

        return redirect('gestionar_productos')

    return render(request, 'admin_alpatex/gestion_productos.html', {
        'productos_pendientes': productos_pendientes
    })



@login_required
def reporte_productos(request):
    productos = Producto.objects.all()

    # Filtrado por nombre de producto
    nombre = request.GET.get('nombre', '')
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)

    # Filtrado por fecha de creación
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    if fecha_inicio and fecha_fin:
        productos = productos.filter(fecha_creacion__range=[fecha_inicio, fecha_fin])

    # Filtrado por nombre de usuario
    nombre_usuario = request.GET.get('usuario', '')
    if nombre_usuario:
        productos = productos.filter(usuario__username__icontains=nombre_usuario)

    # Si el parámetro "exportar" está presente en la URL, generar el archivo Excel
    if request.GET.get('exportar', '') == 'excel':
        return export_to_excel(request)

    return render(request, 'admin_alpatex/reporte_productos.html', {'productos': productos})



def export_to_excel(request):
    # Crea un libro de trabajo de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte de Productos"
    
    # Títulos de las columnas
    ws.append(['Nombre', 'Usuario', 'Fecha de Creación', 'Dirección', 'Estado de Revisión', 'Motivo de Rechazo'])
    
    # Obtener los productos desde la base de datos
    productos = Producto.objects.all()

    # Añadir los datos a las filas
    for producto in productos:
        ws.append([ 
            producto.nombre,
            producto.usuario.username,
            producto.fecha_creacion.strftime('%d %b %Y'),
            producto.usuario.perfil.direccion,
            producto.estado_revision,
            producto.motivo_rechazo if producto.estado_revision == 'Rechazado' else 'N/A',
        ])
    
    # Crea una respuesta HTTP para descargar el archivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=report.xlsx'
    wb.save(response)
    return response


def usuarios(request):
    usuarios = User.objects.all()  # Recupera todos los usuarios registrados
    return render(request, 'admin_alpatex/usuarios.html', {'usuarios': usuarios})


@login_required
def perfil_usuario(request, username):
    # Obtener el usuario y su perfil
    usuario = get_object_or_404(User, username=username)
    perfil = get_object_or_404(Perfil, user=usuario)

    return render(request, 'admin_alpatex/perfil.html', {'perfil': perfil})
