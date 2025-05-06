from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from index.models import Producto, Perfil
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import openpyxl
from django.http import HttpResponse
from datetime import datetime
from .models import Membresia
from .forms import MembresiaForm


def dashboard(request):
    return render(request, 'admin_alpatex/home_admin.html')

def home_admin(request):
    usuarios = User.objects.all()
    productos = Producto.objects.all()  # Obtener todos los productos
    context = {"usuarios": usuarios, "productos": productos}  # Pasar la variable 'productos'
    return render(request, 'admin_alpatex/home_admin.html', context)

@login_required
def menu(request):
    request.session["usuario"]="cgarcia"
    usuario=request.session["usuario"]
    context={'usuario':usuario}
    return render(request, 'admin_alpatex/home_admin.html', context)




def gestionar_productos(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        accion = request.POST.get('accion')
        print(f"Producto ID recibido: {producto_id}, Acción: {accion}")

        # Validar si viene producto_id vacío
        if not producto_id:
            messages.error(request, "Error: No se recibió el ID del producto.")
            return redirect('gestionar_productos')

        producto = get_object_or_404(Producto, id_producto=producto_id)

        if accion == 'aceptar':
            producto.estado_revision = 'Aceptado'
            producto.save()
            messages.success(request, "Producto aceptado correctamente.")
        elif accion == 'rechazar':
            motivo = request.POST.get('motivo')
            if motivo:
                producto.estado_revision = 'Rechazado'
                producto.motivo_rechazo = motivo
                producto.save()
                messages.success(request, "Producto rechazado correctamente.")
            else:
                messages.error(request, "Debes indicar el motivo de rechazo.")
        else:
            messages.error(request, "Acción no válida.")

        return redirect('gestionar_productos')

    # Obtener productos pendientes y ordenarlos por prioridad
    productos_pendientes = Producto.objects.filter(estado_revision='Pendiente')
    productos_pendientes = sorted(productos_pendientes, key=lambda p: p.prioridad_verificacion)

    return render(request, 'admin_alpatex/gestion_productos.html', {'productos_pendientes': productos_pendientes})

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
    usuarios = User.objects.select_related('perfil').all()  # Carga los perfiles de manera eficiente
    return render(request, 'admin_alpatex/usuarios.html', {'usuarios': usuarios})


@login_required
def perfil_usuario(request, username):
    # Obtener el usuario y su perfil
    usuario = get_object_or_404(User, username=username)
    perfil = get_object_or_404(Perfil, user=usuario)

    return render(request, 'admin_alpatex/perfil.html', {'perfil': perfil})


#Membresias
# Listado
def listar_membresias(request):
    membresias = Membresia.objects.all()
    return render(request, 'admin_alpatex/membresia_list.html', {'membresias': membresias})

# Crear
def crear_membresia(request):
    if request.method == 'POST':
        form = MembresiaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_membresias')
    else:
        form = MembresiaForm()
    return render(request, 'admin_alpatex/membresia_form.html', {'form': form})

# Editar
def editar_membresia(request, membresia_id):
    membresia = get_object_or_404(Membresia, pk=membresia_id)
    if request.method == 'POST':
        form = MembresiaForm(request.POST, instance=membresia)
        if form.is_valid():
            form.save()
            return redirect('listar_membresias')
    else:
        form = MembresiaForm(instance=membresia)
    return render(request, 'admin_alpatex/membresia_form.html', {'form': form})

# Eliminar
def eliminar_membresia(request, membresia_id):
    membresia = get_object_or_404(Membresia, pk=membresia_id)
    membresia.delete()
    return redirect('listar_membresias')