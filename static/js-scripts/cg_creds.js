$(document).ready(function() {
    $('#cargar').on('click', function() {
        // Realizar la solicitud AJAX al servidor para escanear la red
        $.ajax({
            url: '/cargar_credenciales',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Limpiar la tabla antes de agregar nuevos datos
                $('#credenciales').empty();
                // Verificar si data está definido y es iterable
                if (Array.isArray(data)) {
                  // Agregar datos escaneados a la tabla
                  console.log(data);
                  data.forEach(function(credencial) {
                    if ((credencial.user === '') || (credencial.user === ' ')){
                      credencial.user = '          ';
                    }

                    $('#credenciales').append(`
                        <div class="tarjeta-cred">
                          <div class="estatico">
                            <p>Sitio Web:</p>
                            <p>Usuario:</p>
                            <p>Email:</p>
                            <p>Contraseña:</p>
                            <p>Descripción:</p>
                          </div>

                          <div class="dinamico">
                            <p>${credencial.site}</p>
                            <p>${credencial.user}</p>
                            <p>${credencial.email}</p>
                            <p>${credencial.password}</p>
                            <p>${credencial.description}</p>
                          </div>
                        </div>
                      `);
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
