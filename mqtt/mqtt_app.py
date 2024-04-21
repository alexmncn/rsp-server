# mqtt_app.py
import sys
import os

# Obtener la ruta del directorio que contiene el módulo app
app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Agregar la ruta al sys.path
sys.path.append(app_path)

import threading
import json
import paho.mqtt.client as mqtt
from datetime import datetime
from send_notis import send_noti
from app import app, db, SensorData
from config import MQTT_Service

# Configuración del servidor MQTT
MQTT_HOST = MQTT_Service.HOST
MQTT_PORT = MQTT_Service.PORT
MQTT_CLIENT_ID = MQTT_Service.CLIENT_ID
MQTT_KEEP_ALIVE = 60

# Ruta al certificado CA
CA_CERTIFICATE = MQTT_Service.CA_CERTIFICATE


def insert_sensor_data(sensor_name, temperature, humidity, date):
    with app.app_context():
        new_data = SensorData(sensor_name=sensor_name, temperature=temperature, humidity=humidity, date=date)
        db.session.add(new_data)
        db.session.commit()


# Función para manejar los mensajes recibidos
def on_message(client, userdata, message):
    # Obtener el mensaje en formato JSON
    message_data = json.loads(message.payload.decode())

    # Obtener los datos del mensaje
    sensor_name = message_data["sensor"]
    temperature = message_data["temp"]
    humidity = message_data["humd"]
    date_str = message_data.get("date")
    date = datetime.strptime(date_str, "%d-%m-%Y %H:%M:%S") if date_str else None

    # Insertar los datos en la base de datos
    insert_sensor_data(sensor_name, temperature, humidity, date)

    # Enviar notificación
    #send_noti(debug, 'default')


# Función para iniciar el cliente MQTT y suscribirse a un tema
def start_mqtt_subscription():
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID, clean_session=False)
    mqtt_client.tls_set(CA_CERTIFICATE)

    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEP_ALIVE)
    # Suscribirse al tema
    topic = "test/topic"
    mqtt_client.subscribe(topic, qos=2)  # QoS 2 para garantizar la entrega exactamente una vez

    # Iniciar la recepción de mensajes
    mqtt_client.loop_forever()


# Ejecutar la suscripción MQTT en un hilo separado
mqtt_thread = threading.Thread(target=start_mqtt_subscription)
mqtt_thread.daemon = True
mqtt_thread.start()
start_mqtt_subscription()
