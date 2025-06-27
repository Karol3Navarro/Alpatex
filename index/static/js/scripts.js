console.log("scripts.js cargado");

// Variables globales para almacenar la membresía y el precio seleccionados
let membresiaSeleccionada = null;
let precioSeleccionado = null;
let cardForm = null;

// Hacer cardForm disponible globalmente
window.cardForm = cardForm;

document.addEventListener("DOMContentLoaded", function(){
  new Swiper(".mySwiper", {
    slidesPerView: 4,
    spaceBetween: 20,
    loop: true,
    navigation: {
      nextEl: ".swiper-button-next",
      prevEl: ".swiper-button-prev",
    },
    breakpoints: {
      1024: {slidesPerView: 4},
      768: {slidesPerView: 2},
      680: {slidesPerView: 1},
    }
  });
});

//FUNCION PARA QUE SE DESPLIEGUE PRECIO
document.addEventListener("DOMContentLoaded", function () {
  const tipoSelect = document.getElementById("id_tipo");
  const precioWrapper = document.getElementById("precio-wrapper");
  const precioInput = document.getElementById("id_precio");

  function togglePrecio() {
    if (tipoSelect.value === "Venta") {
      precioWrapper.style.display = "block";
    } else {
      precioWrapper.style.display = "none";
      if (precioInput) {
        precioInput.value = "";  // Limpia si no es venta
      }
    }
  }

  if (tipoSelect && precioWrapper) {
    tipoSelect.addEventListener("change", togglePrecio);
    togglePrecio();  // Asegura que esté correcto en el primer renderizado
  }
});

//FUNCION PARA LAS ALERTAS
document.addEventListener("DOMContentLoaded", function () {
  const alerts = document.querySelectorAll(".alert:not([id='mensaje-cancelacion'])");
  setTimeout(() => {
    alerts.forEach(alert => {
      alert.classList.add("alert-hidden");
    });
  }, 3000);
});

//CONFIRMACION DE ELIMINAR PRODUCTO PERFIL USUARIO (SWEETALERT2)
document.addEventListener("DOMContentLoaded", () => {
  const eliminarLinks = document.querySelectorAll(".btn-eliminar");

  eliminarLinks.forEach(link => {
    link.addEventListener("click", function (e) {
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
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll('.btn-mem-del').forEach(function (button) {
    button.addEventListener('click', function (e) {
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

//FUNCION PARA DESPLEGAR MAS OPCIONES
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".toggle-btn").forEach(button => {
    button.addEventListener("click", function (e) {
      e.stopPropagation();

      const menu = this.closest(".producto-card").querySelector(".drop-opc");

      document.querySelectorAll(".drop-opc").forEach(m => {
        console.log("Boton activado")
        if (m !== menu) {
          m.style.display = "none";
        }
      });

      // Alternar el menú actual
      menu.style.display = (menu.style.display === "block") ? "none" : "block";
    });
  });

  document.addEventListener("click", () => {
    document.querySelectorAll(".drop-opc").forEach(menu => {
      menu.style.display = "none";
    });
  });
});


//FUNCION PARA EL FILTRO DE PRODUCTOS.HTML
document.addEventListener("DOMContentLoaded", function () {
  const filtros = document.querySelectorAll('input[type="radio"]');
  filtros.forEach(filtro => {
    filtro.addEventListener('change', aplicarFiltros);
  });

  const btnLimpiar  = document.getElementById("limp-filt");
  if (btnLimpiar) {
    btnLimpiar.addEventListener("click", function () {
      filtros.forEach(r => r.checked = false);

      const productos = document.querySelectorAll('.producto-card-link');
      productos.forEach(producto => {
        producto.style.display = "block";
      });
    });
  }
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

//FUNCION PARA EDITAR PRODUCTOS
const editables = [
  "username_input",
  "email_input",
  "genero_input",
  "foto_perfil_input",
  "direccion_input"
];

function toggleEdit(modo) {
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

// FUNCIÓN PARA EDITAR LA INFORMACIÓN DE UN PRODUCTO
function toggleEditProducto(modo, productoId) {
  console.log("Modo edición del producto:", modo);

  const editables = document.querySelectorAll(`#producto-${productoId} .editable`);
  const btn = document.getElementById(`btn-editar-producto-${productoId}`);

  editables.forEach(el => {
    el.disabled = !modo;
  });

  if (modo) {
    btn.textContent = "Cancelar edición";
    btn.setAttribute("onclick", `toggleEditProducto(false, ${productoId})`);
  } else {
    btn.textContent = "Editar producto";
    btn.setAttribute("onclick", `toggleEditProducto(true, ${productoId})`);
  }
}

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


function abrirModal() {
  document.getElementById("modRecContra").style.display = "block";
}

function cerrarModal() {
  document.getElementById("modRecContra").style.display = "none";
}


// Función para inicializar MercadoPago
function inicializarMercadoPago() {
  console.log("=== INICIANDO INICIALIZACIÓN DE MERCADOPAGO ===");
  
  // 1) Valida que la llave esté definida
  if (typeof MERCADOPAGO_PUBLIC_KEY === 'undefined' || !MERCADOPAGO_PUBLIC_KEY) {
    console.error("MERCADOPAGO_PUBLIC_KEY no está definida");
    return;
  }
  console.log("MERCADOPAGO_PUBLIC_KEY:", MERCADOPAGO_PUBLIC_KEY);

  // 2) Valida que MercadoPago esté disponible
  if (typeof MercadoPago === 'undefined') {
    console.error(" El SDK de MercadoPago no está cargado");
    return;
  }
  console.log("SDK de MercadoPago disponible");

  console.log("Creando instancia de MercadoPago...");
  const mp = new MercadoPago(MERCADOPAGO_PUBLIC_KEY, { locale: 'es-CL' });
  console.log("Instancia de MercadoPago creada:", mp);

  // 3) Verifica que el formulario existe
  const formPago = document.getElementById("form-pago");
  if (!formPago) {
    console.error("No se encontró el formulario con id 'form-pago'");
    return;
  }
  console.log("Formulario encontrado:", formPago);

  // 4) Crea el cardForm de Mercado Pago
  try {
    console.log("Creando cardForm...");
    cardForm = mp.cardForm({
      amount: "0",
      autoMount: true,
      form: {
        id: "form-pago",
        cardholderName: {
          id: "form-checkout__cardholderName",
          placeholder: "Nombre del titular de la tarjeta"
        },
        cardholderEmail: {
          id: "form-checkout__cardholderEmail",
          placeholder: "E-mail"
        },
        cardNumber: {
          id: "form-checkout__cardNumber",
          placeholder: "Número de tarjeta (ej: 5031 7557 3453 0604)"
        },
        expirationDate: {
          id: "form-checkout__expirationDate",
          placeholder: "MM/YY (ej: 12/27)"
        },
        securityCode: {
          id: "form-checkout__securityCode",
          placeholder: "CVV (ej: 123)"
        },
        installments: {
          id: "form-checkout__installments",
          placeholder: "Cuotas"
        },
        identificationType: {
          id: "form-checkout__identificationType",
          placeholder: "Tipo de documento"
        },
        identificationNumber: {
          id: "form-checkout__identificationNumber",
          placeholder: "DNI (ej: 12345678-9)"
        },
        issuer: {
          id: "form-checkout__issuer",
          placeholder: "Banco emisor"
        }
      },
      callbacks: {
        onFormMounted: (error) => {
          if (error) {
            console.warn("Error montando el cardForm:", error);
          } else {
            console.log("Formulario de pago montado correctamente");
          }
        },
        onSubmit: (event) => {
          event.preventDefault();
          procesarPago();
        },
        onFetching: (resource) => {
          console.log("Fetching recurso:", resource);
        },
        onError: (error) => {
          // Si el error es sobre cuotas/payer_costs, no se muestra nada al usuario
          let mensaje = error && error.message ? error.message : JSON.stringify(error);
          if (
            mensaje.includes("payer_costs") ||
            mensaje.includes("installments") ||
            mensaje.includes("Failed to get installments") ||
            mensaje.includes("Cannot destructure property 'payer_costs'")
          ) {
            // No mostramos nada, es un error esperado en Sandbox o sin cuotas
            return;
          }
          // Para cualquier otro error, si se muestra
          console.error("Error en cardForm:", error);
          document.getElementById('form-result').innerHTML =
            `<div class="alert alert-error">Error en el formulario de pago: ${mensaje}</div>`;
        }
      }
    });
    
    // Actualizar tanto la variable local como la global
    window.cardForm = cardForm;
    
    console.log("cardForm creado exitosamente:", cardForm);
    console.log("=== INICIALIZACIÓN DE MERCADOPAGO COMPLETADA ===");
  } catch (error) {
    console.error("Error al crear cardForm:", error);
  }
}

// Hacer la función disponible globalmente
window.inicializarMercadoPago = inicializarMercadoPago;

// esperar a que el dom este elisto
document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM cargado, verificando MercadoPago...");
  console.log("MERCADOPAGO_PUBLIC_KEY disponible:", typeof MERCADOPAGO_PUBLIC_KEY !== 'undefined');
  console.log("MercadoPago SDK disponible:", typeof MercadoPago !== 'undefined');
  
  // Verifica que MercadoPago  está cargado
  if (typeof MercadoPago !== 'undefined') {
    console.log("MercadoPago ya está cargado, inicializando...");
    inicializarMercadoPago();
  } else {
    console.log("MercadoPago no está cargado, esperando...");
    // si no esta cargado, se espera a que  cargue
    const checkMercadoPago = setInterval(() => {
      if (typeof MercadoPago !== 'undefined') {
        console.log("MercadoPago cargado, inicializando...");
        clearInterval(checkMercadoPago);
        inicializarMercadoPago();
      }
    }, 100);

    // Timeout de seguridad  10 segundos
    setTimeout(() => {
      clearInterval(checkMercadoPago);
      if (typeof MercadoPago === 'undefined') {
        console.error("No se pudo cargar el SDK de MercadoPago después de 10 segundos");
      }
    }, 10000);
  }
});

// También intentar inicializar cuando se carga la ventana
window.addEventListener('load', function() {
  console.log("Ventana cargada, verificando MercadoPago...");
  console.log("MercadoPago SDK disponible en window.load:", typeof MercadoPago !== 'undefined');
  if (typeof MercadoPago !== 'undefined' && !cardForm) {
    console.log("MercadoPago disponible en window.load, inicializando...");
    inicializarMercadoPago();
  }
});

// 4) Limpia el contenido del modal (resetea campos y elimina mensajes)
function limpiarModal() {
  const formResult = document.getElementById("form-result");
  const formPago = document.getElementById("form-pago");
  
  if (formResult) {
    formResult.innerHTML = "";
  }
  
  if (formPago) {
    formPago.reset();
  }
}

// Hacer la función disponible globalmente
window.limpiarModal = limpiarModal;

// 5) Lógica para procesar el pago tras generar el token
async function procesarPago() {
  console.log("=== INICIANDO PROCESAR PAGO ===");
  console.log("window.membresiaSeleccionada al inicio:", window.membresiaSeleccionada);
  console.log("window.precioSeleccionado al inicio:", window.precioSeleccionado);
  
  const formData = window.cardForm.getCardFormData();
  console.log("Datos del formulario:", formData);

  if (!formData.token) {
    console.warn("No se generó ningún token de tarjeta.");
    document.getElementById('form-result').innerHTML =
      `<div class="alert alert-error">Error: No se pudo generar el token de la tarjeta</div>`;
    return;
  }

  console.log("Token de tarjeta generado correctamente:", formData.token);

  const payload = {
    token_tarjeta: formData.token,
    membresia_id: window.membresiaSeleccionada
  };

  console.log("Payload que se enviará al backend:", payload);
  console.log("window.membresiaSeleccionada:", window.membresiaSeleccionada);

  try {
    const response = await fetch('/index/membresia/api/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(payload)
    });

    console.log("Respuesta del servidor:", response.status, response.statusText);
    
    const data = await response.json();
    console.log("Datos de respuesta:", data);
    
    if (response.status === 200 && data.init_point) {
      console.log("Redirigiendo a:", data.init_point);
      window.location.href = data.init_point;
    } else {
      console.error("Error del backend:", data.error || JSON.stringify(data));
      document.getElementById('form-result').innerHTML =
        `<div class="alert alert-error">${data.error || "Error desconocido"}</div>`;
    }
  } catch (err) {
    console.error("Error en la petición al backend:", err);
    document.getElementById('form-result').innerHTML =
      `<div class="alert alert-error">Error al procesar el pago: ${err}</div>`;
  }
}

// 6) Obtener cookie CSRF en Django
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.getElementById('confirmar-cancelacion').addEventListener('click', function () {
  fetch('/index/membresia/cancelar/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/json'
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Muestra el modal Bootstrap con el mensaje
        document.getElementById('modalMensajeBody').innerText = '¡Tu plan ha sido cancelado! Seguirá activo hasta la fecha de vencimiento.';
        var modalMensaje = new bootstrap.Modal(document.getElementById('modalMensaje'));
        modalMensaje.show();

        // Al cerrar el modal, oculta el botón y muestra el mensaje destacado
        document.getElementById('modalMensaje').addEventListener('hidden.bs.modal', function handler() {
          // Oculta el botón y el formulario
          var formCancelar = document.getElementById('form-cancelar-plan');
          if (formCancelar) {
            formCancelar.style.display = 'none';
          }
          // Muestra el mensaje destacado
          var mensajeDiv = document.getElementById('mensaje-cancelacion');
          if (mensajeDiv) {
            mensajeDiv.style.display = 'block';
            mensajeDiv.innerHTML = `
                      <div class="alert alert-warning" style="font-weight:bold;">
                        Tu plan fue cancelado y estará activo hasta que se cumpla un mes desde el último pago válido.
                      </div>
                    `;
          }
          // Elimina el listener para evitar duplicados
          document.getElementById('modalMensaje').removeEventListener('hidden.bs.modal', handler);
        });
      } else {
        // Muestra el error en el modal también
        document.getElementById('modalMensajeBody').innerText = 'Error: ' + data.error;
        var modalMensaje = new bootstrap.Modal(document.getElementById('modalMensaje'));
        modalMensaje.show();
      }
    });

  // Cierra el modal de Bootstrap
  var modal = bootstrap.Modal.getInstance(document.getElementById('modalCancelar'));
  modal.hide();
});

console.log("ANTES de definir mostrarFormularioPago");

window.mostrarFormularioPago = function (membresiaId, precio) {
  console.log("Función mostrarFormularioPago llamada con:", membresiaId, precio);

  // Usar las variables globales window
  window.membresiaSeleccionada = membresiaId;
  window.precioSeleccionado = precio;

  console.log("window.membresiaSeleccionada configurada como:", window.membresiaSeleccionada);
  console.log("window.precioSeleccionado configurado como:", window.precioSeleccionado);

  const modal = document.getElementById("modal-pago");
  if (!modal) {
    console.error("No se encontró el modal de pago");
    alert("Error: No se encontró el modal de pago");
    return;
  }

  // Limpia cualquier <input name=\"membresia_id\"> previo
  const formPago = document.getElementById("form-pago");
  if (!formPago) {
    console.error("No se encontró el formulario de pago");
    alert("Error: No se encontró el formulario de pago");
    return;
  }

  const prevHidden = formPago.querySelector('input[name=\"membresia_id\"]');
  if (prevHidden) {
    prevHidden.remove();
  }

  // Inserta el campo hidden con el ID de la membresía
  const membresiaInput = document.createElement("input");
  membresiaInput.type = "hidden";
  membresiaInput.name = "membresia_id";
  membresiaInput.value = membresiaId;
  formPago.appendChild(membresiaInput);

  // Mostramos el modal
  modal.style.display = "flex";
  console.log("Modal mostrado exitosamente");

  // Al hacer clic en la X, cerramos y limpiamos
  const cerrarBtn = modal.querySelector(".cerrar");
  if (cerrarBtn) {
    cerrarBtn.onclick = function () {
      modal.style.display = "none";
      if (typeof window.limpiarModal === 'function') {
        window.limpiarModal();
      }
    };
  }

  // Al hacer clic fuera del contenido, también cerramos
  window.onclick = function (event) {
    if (event.target == modal) {
      modal.style.display = "none";
      if (typeof window.limpiarModal === 'function') {
        window.limpiarModal();
      }
    }
  };

  // Verificar si cardForm está disponible
  if (!window.cardForm) {
    console.warn("cardForm no está inicializado. El formulario de pago puede no funcionar correctamente.");
    const formResult = document.getElementById('form-result');
    if (formResult) {
      formResult.innerHTML = '<div class="alert alert-warning">Inicializando formulario de pago...</div>';
    }
  }
};


console.log("DESPUÉS de definir mostrarFormularioPago");