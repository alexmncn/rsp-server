# /var/www/html/wsgi/app_ssl.wsgi

import sys
import site

sys.path.insert(0, '/var/www/html/')  # Agrega la ruta de tu proyecto

from app import app  # Importa la aplicación Flask desde app.py

application = app  # Asigna la aplicación a la variable application (importante para mod_wsgi)
