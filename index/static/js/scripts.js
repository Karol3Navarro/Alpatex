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
                alert("Un error ocurrió, por favor intenta nuevamente");
            }
        };

        xhr.send(formData); // Envia los datos al servidor
    });
});
