// static/js/mapa.js

// Inicializar el mapa en Santiago de Chile
var map = L.map('map').setView([-33.4489, -70.6693], 12);

// Cargar el tile de OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Función para buscar coordenadas en Nominatim
async function buscarCoordenadas(direccion) {
    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(direccion)}`);
    const data = await response.json();
    if (data.length > 0) {
        return [parseFloat(data[0].lat), parseFloat(data[0].lon)];
    }
    return null;
}

// Mostrar productos en el mapa
async function mostrarProductos() {
    try {
        for (const producto of window.perfiles) {  // ← ahora son productos
            const coords = await buscarCoordenadas(producto.direccion);
            if (coords) {
                L.marker(coords)
                    .addTo(map)
                    .bindPopup(`
                        <b>${producto.nombre}</b><br>
                        ${producto.direccion}<br>
                        <a href="/index/producto/${producto.id}/" class="btn btn-primary mt-2">Ver Detalle</a>
                    `)
            }
        }
    } catch (error) {
        console.error('Error mostrando productos:', error);
    }
}

// Llamar a la función
mostrarProductos();