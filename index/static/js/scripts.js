// scripts.js

document.addEventListener("DOMContentLoaded", () => {
    const MsgForm = document.getElementById("form_submit");
    const msgContainer = document.getElementById("contenedor_ms");

    // Evento de envío del formulario
    MsgForm.addEventListener("submit", (event) => {
        event.preventDefault(); // Detiene la opción predeterminada del formulario

        const targetDate = event.target; // Recibe los datos enviados del formulario
        const formData = new FormData(targetDate); // Construye la lista de datos

        const xhr = new XMLHttpRequest(); // XMLHttpRequest para realizar la petición AJAX

        const endpoint = MsgForm.getAttribute("action");
        const method = MsgForm.getAttribute("method");
        xhr.open(method, endpoint);

        xhr.responseType = 'json';

        xhr.setRequestHeader("HTTP_X_REQUESTED_WITH", "XMLHttpRequest");
        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

        xhr.onload = () => {
            console.log(xhr.status, xhr.response);

            if (xhr.status === 201) {
                const respuestaData = xhr.response;
                let actualMensajeHtml = msgContainer.innerHTML;
                actualMensajeHtml += `<div class=''><b>${respuestaData.username}</b><p>${respuestaData.mensaje}</p></div>`; 
                msgContainer.innerHTML = actualMensajeHtml; // Actualiza el contenedor de mensajes
                MsgForm.reset();
                location.reload(); // Recarga la página para mostrar el nuevo mensaje
            } else if (xhr.status === 400) {
                console.log(xhr.response);
            } else {
                alert("Error, por favor intenta nuevamente");
            }
        };

        xhr.send(formData); // Envia los datos al servidor
    });
});

const editables = [
    "username_input",
    "email_input",
    "genero_input",
    "foto_perfil_input",
    "direccion_input"
];

function toggleEdit(modo){
    console.log("Modo edición:", modo);
    editables.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = !modo;
    });

    document.getElementById("label_foto_perfil").style.display = modo ? "block" : "none"; 
    document.getElementById("foto_perfil_input").style.display = modo ? "inline-block" : "none";  
    document.getElementById("guardar_editar").style.display = modo ? "inline-block" : "none";

    const btn = document.getElementById("btn_editar");
    if (modo) {
        btn.textContent = "Cancelar edición";
        btn.setAttribute("onclick", "toggleEdit(false)");
    } else {
        btn.textContent = "Editar perfil";
        btn.setAttribute("onclick", "toggleEdit(true)");
    }
}

function abrirModal(){
    document.getElementById("modRecContra").style.display = "block";
}

function cerrarModal(){
    document.getElementById("modRecContra").style.display = "none";
}
//FUNCION PARA EDITAR LA INFORMACION DE UN PRODUCTO
function toggleEditProducto(modo, productoId) {
    console.log("Modo edición del producto:", modo);

    const editables = document.querySelectorAll(`#producto-${productoId} .editable`);
    editables.forEach(el => {
        el.disabled = !modo;  // Habilitar o deshabilitar el campo
    });

    const btn = document.getElementById(`btn-editar-producto-${productoId}`);
    if (modo) {
        btn.textContent = "Cancelar edición";
        btn.setAttribute("onclick", `toggleEditProducto(false, ${productoId})`);
    } else {
        btn.textContent = "Editar producto";
        btn.setAttribute("onclick", `toggleEditProducto(true, ${productoId})`);
    }
}

//FUNCION PARA EL FILTRO DE PRODUCTOS.HTLM 
document.addEventListener("DOMContentLoaded", function () {
const filtros = document.querySelectorAll('input[type="radio"]');
filtros.forEach(filtro => {
    filtro.addEventListener('change', aplicarFiltros);
});

    function aplicarFiltros() {
        const categoria = document.querySelector('input[name="categoria"]:checked')?.value;
        const estado = document.querySelector('input[name="estado"]:checked')?.value;
        const tipo = document.querySelector('input[name="tipo"]:checked')?.value;

        const productos = document.querySelectorAll('.producto-card-link');

        productos.forEach(producto => {
        const matchCategoria = !categoria || producto.dataset.categoria === categoria;
        const matchEstado = !estado || producto.dataset.estado === estado;
        const matchTipo = !tipo || producto.dataset.tipo === tipo;

        if (matchCategoria && matchEstado && matchTipo) {
            producto.style.display = "block";
        } else {
            producto.style.display = "none";
        }
        });
    }
});

//FUNCION PARA LAS ALERTAS
document.addEventListener("DOMContentLoaded", function(){
    const alerts = document.querySelectorAll(".alert");
    setTimeout(() => {
        alerts.forEach(alert => {
            alert.classList.add("alert-hidden");
        });
    }, 3000);
});

//FUNCION PARA DESPLEGAR MAS OPCIONES
document.addEventListener("DOMContentLoaded",() => {
    document.querySelectorAll(".toggle-btn").forEach(button => {
        button.addEventListener("click", function(e){
            e.stopPropagation();
            const menu = this.closest(".producto-card").querySelector(".drop-opc");
            document.querySelectorAll(".drop-opc").forEach(m => {
                if (m !== menu) m.style.display = "none";
            });
            menu.style.display = (menu.style.display === "block") ? "none" : "block";
        });
    });

    document.addEventListener("click", () =>{
        document.querySelectorAll(".drop-opc").forEach(menu => {
            menu.style.display = "none";
        });
    });
});

//PREVISUALIZACION DE IMAGENES PARA SUBIR PRODUCTO
document.addEventListener("DOMContentLoaded", () => {
    const imgInput = document.getElementById('id_imagen');
    const prevImg = document.getElementById('img-previa');
    
    if (imgInput) {
        imgInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (event) {
                    prevImg.src = event.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
});


//CONFIRMACION DE ELIMINAR PRODUCTO PERFIL USUARIO (SWEETALERT2)
document.addEventListener("DOMContentLoaded", () => {
    const eliminarLinks = document.querySelectorAll(".btn-eliminar");

    eliminarLinks.forEach(link => {
        link.addEventListener("click", function(e) {
        e.preventDefault();
        const url = this.getAttribute("data-url");

        Swal.fire({
            title: "¿Estás seguro?",
            text: "Esta acción no se puede deshacer.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#d33",
            cancelButtonColor: "#3085d6",
            confirmButtonText: "Sí, eliminar",
            cancelButtonText: "Cancelar"
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = url;
            }
        });
        });
    });
});

//ALERTA PARA CONFIRMAR ELIMINAR MEMBRESIA
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.btn-mem-del').forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const url = this.getAttribute('href');

            Swal.fire({
                title: '¿Estás seguro?',
                text: "Esta acción no se puede deshacer.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;
                }
            });
        });
    });
});