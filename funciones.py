#funciones.py
import subprocess
import requests
import check_status, access_log, send_notis
from access_log import access_log_table
from sqlalchemy import desc, func
import json
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from config import ESP32
import csv, time

ip_pc_piso = '192.168.1.53' #IP piso
ip_pc_casa = '192.168.0.12' #IP ip_pc_casa

guardar_datos_sensor = True

#estado dispositivos
def check_device_connection(ip_address):
    try:
        result = subprocess.run(['ping','-c', '1','-W','1', ip_address],stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        if "0% packet loss" in result.stdout:
            return f"Conectado"
        else:
            return f"Desconectado"
    except subprocess.CalledProcessError:
        return f"Desconectado"


#ejecutar script/comando
def ejecutar_script(comando):
    try:
        output = subprocess.check_output(comando, shell=True, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
        return output
    except subprocess.CalledProcessError as e:
        return e.output


#Encender PC a traves de petición a ESP
def pc_on_esp32():
    #Obtenemos la ip local y comprobamos el 3 octeto para verificar que red estamos
    ip_local = get_local_ip()
    octeto_3 = int(ip_local.split('.')[2]) #la 'ip_esp' ya esta definida al principio con f string para añadir el valor de 'octeto_3'
    ip_esp = f'192.168.{octeto_3}.100'

    url_web_esp_on = f'http://{ip_esp}/control?secret_class={ESP32.ON_KEY}&on=ON'

    #comprobamos el estado del pc y procedemos según éste
    current_status = pc_status()

    if current_status == 'ACTIVO':
        return 'El PC ya está encendido'
    else:
        return peticion_get(url_web_esp_on)

# Obtiene y devuelve la temperatura y la humedad obtenida del sensor conectado al esp32
def temperature_and_humidity_dht22():
    ip_local = get_local_ip()
    octeto_3 = int(ip_local.split('.')[2])
    ip_esp = f'192.168.{octeto_3}.100'

    url_web_esp_th = f'http://{ip_esp}/getTempAndHumd'
    
    response = requests.get(url_web_esp_th)
    data = response.json()

    temp = round(float(data["temperature"]), 1)
    humd = round(float(data["humidity"]), 1)

    status_json = {
        'temperature':{'status-data': temp},
        'humidity':{'status-data': humd},
    }

    return status_json


#Llama a la funcion que devuelve los datos del sensor y los guarda cada 30 segundos en un .csv
def save_sensor_data_csv():
    time_delay = 30
    send_notis.send_noti(f'Se ha empezado a guardar datos del sensor. Cada {time_delay} seg.', 'default')
    while guardar_datos_sensor:
        datos_sensor = temperature_and_humidity_dht22()

        temperatura = datos_sensor['temperature']['status-data']
        humedad = datos_sensor['humidity']['status-data']
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Guardar los datos en el archivo CSV
        with open('/var/www/html/logs/sensor_data.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([fecha, temperatura, humedad])
        
        # Esperar durante 30 segundos antes de la próxima ejecución
        time.sleep(time_delay)

    send_notis.send_noti('Se ha parado el guardado de datos del sensor.', 'default')



#pc status 
def pc_status():
    ip_local = get_local_ip()
    octeto_3 = int(ip_local.split('.')[2])
    
    if octeto_3 == 0:
        ip_pc = ip_pc_casa
    else: ip_pc = ip_pc_piso

    return check_device_connection(ip_pc)


# Ejecuta el comando y obtiene el uso de CPU total
def get_cpu_usage():
    # Ejecutar el comando 'sar -u' y capturar la salida
    resultado = subprocess.run(['sar', '-u', '1', '1'], capture_output=True, text=True)

    # Obtener las líneas de salida
    lineas = resultado.stdout.split('\n')

    # Inicializar una lista para almacenar los porcentajes de uso de CPU
    porcentajes_cpu = []

    # Recorrer las líneas y extraer los porcentajes de uso de CPU
    for linea in lineas:
        # Dividir la línea en columnas
        columnas = linea.split()
        # Verificar si hay columnas y si la primera columna es 'all'
        if len(columnas) > 0 and columnas[1] == 'all':

            for columna in columnas[2:7]:
                # Obtener el porcentaje de uso de CPU y convertirlo a flotante
                porcentaje_cpu = float(columna)
                # Agregar el porcentaje a la lista
                porcentajes_cpu.append(porcentaje_cpu)

    # Sumar los porcentajes de uso de CPU
    total_cpu_usage = sum(porcentajes_cpu)

    # Imprimir el uso total de CPU
    return total_cpu_usage


#obtener_datos_json_tablas
def datos_status_tabla1():
    status_miquel = check_status.miquel()
    status_noe = check_status.noe()
    status_iphone = check_status.iphone()

    status_json = {
        'miquel': {'columnaSTATUS': status_miquel},
        'noe': {'columnaSTATUS': status_noe},
        'iphone': {'columnaSTATUS': status_iphone},
    }

    return status_json


#obtener datos tabla 3 raspberry server
def datos_status_tabla3():
    temp = int(float(ejecutar_script('cat /sys/class/thermal/thermal_zone0/temp'))/1000)
    rsp_temp = f'{temp} ºC'

    cpu = round(float(get_cpu_usage()), )
    cpu_usage = f'{cpu} %'

    status_json = {
        'temp': {'status-data': rsp_temp},
        'cpu-usage':{'status-data': cpu_usage},
    }

    return status_json


def datos_status_tabla4():
    pc_status_ = pc_status()
    #send_notis.send_noti(pc_stats, 'default')

    status_json = {
        'pc-status': {'status-data': pc_status_},
    }
    
    return status_json


def last_access_log_query(limit, ip_filter=None):
    #parametros query
    selects = None
    
    columns = ['id', 'remote_host', 'fecha']
    
    if ip_filter:
        filter = access_log_table.columns.remote_host != f'{ip_filter}'
    else:
        filter = None
    
    order = access_log_table.columns.id.desc()


    resultados = access_log.query(selects=selects, columns=columns, filters=filter, order_by=order, limit=limit)
    
    resultados_list = [dict(row) for row in resultados]
    
    return resultados_list


def most_accesses_by_ip_query(limit):
    time_threshold = datetime.utcnow() - timedelta(hours=24)

    #parametros query
    selects = [access_log_table.c.remote_host,func.count().label('count'),func.max(access_log_table.c.fecha).label('last_access')]
    columns = None
    filters = access_log_table.c.fecha >= time_threshold
    group = access_log_table.c.remote_host
    order = func.count().desc()
    
    resultados = access_log.query(selects=selects, columns=columns, filters=filters, group_by=group, order_by=order, limit=limit)
    
    resultados_list = [dict(row) for row in resultados]
    
    return resultados_list


def save_users_ips(current_user):
    # Obtener el último acceso desde la base de datos
    ultimo_acceso = last_access_log_query(1, None)

    # Verificar si hay resultados
    if ultimo_acceso:
        # Obtener la información relevante (en este caso, la dirección IP remota)
        ip_temp = ultimo_acceso[0]['remote_host']

        # Crear un diccionario para almacenar la información
        data = {
            "username": f'{current_user}',
            "data": {
                "remote_host": ip_temp,
                "fecha": str(datetime.now())
            }
        }

        # Obtener la ruta del archivo
        file_path = '/var/www/html/logs/users_ips_log.json'

        try:
            # Intenta cargar el archivo existente
            with open(file_path, 'r') as json_file:
                user_data = json.load(json_file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            # Si el archivo no existe o está vacío, crea una lista vacía
            user_data = []

        # Agrega la nueva entrada al final de la lista
        user_data.append(data)

        # Guarda la lista actualizada en el archivo
        with open(file_path, 'w') as json_file:
            json.dump(user_data, json_file, indent=2)

        return 'bien'
    else:
        return 'mal'

def get_user_ip(username):
    # Obtener la ruta del archivo
    file_path = '/var/www/html/logs/users_ips_log.json'

    try:
        # Intenta cargar el archivo existente
        with open(file_path, 'r') as json_file:
            user_data = json.load(json_file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        # Si el archivo no existe o está vacío, retorna None
        return None

    # Busca la entrada correspondiente al username
    for entry in reversed(user_data):
        if entry["username"] == username:
            remote_host = entry["data"].get("remote_host", None)
            return remote_host

    # Si no se encuentra el username, retorna None
    return None


# Convertir texto en imagen // Funciona pero no se usa
def text_to_image(text, image_path):
    # Configura la fuente y el tamaño
    font = ImageFont.load_default()

    # Divide el texto en líneas
    lines = text.split('\n')

    # Crea la imagen en blanco
    image = Image.new('RGB', (1, 1), 'white')
    draw = ImageDraw.Draw(image)

    # Calcula el ancho y la altura de la imagen
    max_line_width = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines)
    image_width = max_line_width + 20  # 20 píxeles de margen a cada lado
    image_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines) + 20  # 20 píxeles de margen arriba y abajo

    # Crea la imagen en blanco con las dimensiones calculadas
    image = Image.new('RGB', (image_width, image_height), 'black')
    draw = ImageDraw.Draw(image)

    # Agrega el texto a la imagen
    y = 10  # Comienza con un margen de 10 píxeles
    for line in lines:
        # Usa textbbox para obtener el ancho y alto real de la línea
        text_bbox = draw.textbbox((10, y), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        # Dibuja la línea en la imagen
        draw.text((10, y), line, font=font, fill='white')
        y += text_height

    # Guarda la imagen
    image.save(image_path)


#hacer una peticion get a una dirección específica
def peticion_get(url):
    try:
        #hacemos petición a la url
        response = requests.get(url)
            
        #comprobnamos el codigo de estado de la solicitud
        if response.status_code == 200:
            return 'Petición aceptada'
        else:
            return 'Error'
    except Exception as e:
        return None


# Obtiene la ip de conexión
def get_local_ip():
    try:
        ip = subprocess.check_output(['hostname', '-I']).decode('utf-8').strip()
        return ip.split()[0]  # Tomamos la primera dirección IP de la lista
    except Exception as e:
        print("Error al obtener la IP local:", e)
        return None
