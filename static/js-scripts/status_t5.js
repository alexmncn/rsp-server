// status_t5.js
$(document).ready(function() {
function actualizarTabla5() {
  $.ajax({
    url: "/temp_humd_json",
    type: "GET",
    dataType: "json",
    success: function(data) {
      // Iterar sobre los datos recibidos
      Object.keys(data).forEach(function(obj_columna) {
        // Buscar el elemento de la tabla con el atributo data-id correspondiente
        var fila = $("#tabla5-sens tr[data-id='" + obj_columna + "']");

        // Actualizar las celdas de IP y STATUS si la fila se encuentra
        if (fila.length > 0) {
          fila.find(".status-data").text(data[obj_columna]['status-data']);
        }
      });
    },
    error: function(jqXHR, textStatus, errorThrown) {
      console.log("Error al obtener datos desde Flask:", jqXHR);
    }
  });
}
actualizarTabla5();
// Llamar a la función para actualizar la tabla cada 5000 milisegundos (5 segundos)
setInterval(actualizarTabla5, 5000);
});
