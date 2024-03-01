$(document).ready(function() {
    $('#cargar').on('click', function() {
        // Realizar la solicitud AJAX al servidor para escanear la red
        $.ajax({
            url: '/cargar_credenciales',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Limpiar la tabla antes de agregar nuevos datos
                $('#credenciales tbody').empty();
                // Verificar si data está definido y es iterable
                if (Array.isArray(data)) {
                  // Agregar datos escaneados a la tabla
                  data.forEach(function(credenciales) {
                      $('#credenciales tbody').append(
                          `<tr>
                              <td>${credenciales.site}</td>
                              <td>${credenciales.user}</td>
                              <td>${credenciales.email}</td>
                              <td type="password">${credenciales.password}</td>
                              <td>${credenciales.description}</td>
                              
                          </tr>`
                      );
                  });
                } else {
                  console.error('Error: Datos no válidos recibidos del servidor.');
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.error('Error al extraer los datos de la BD:', errorThrown);
            }
        });
    });
});
