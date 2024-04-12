from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import subprocess
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, String, MetaData, desc
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user, LoginManager, UserMixin
from functools import wraps
import os
import time
from datetime import datetime
import logging
import threading

#importamos funciones
import funciones, send_notis, ip_nmap_scan
from funciones import save_sensor_data_csv, send_sensor_data_thinkspeak

#importamos configuracion
from config import Config, SQL_Alchemy, S_Routes


app = Flask(__name__)


#config
app.config.from_object(Config)
app.config.from_object(SQL_Alchemy)


#login control
login_manager = LoginManager(app)
login_manager.login_view = "login"  # Esto especifica la vista de inicio de sesión


#sql
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#USUARIOS
## Estructura tabla usuarios
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(64), default='user',nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


##REGISTRO
### Formulario registro
class RegistrationForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[InputRequired()])
    password = PasswordField('Contraseña', validators=[InputRequired()])

### Vista de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Verifica si ya existe un usuario con el mismo nombre de usuario
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash ('El nombre de usuario ya está en uso.\nPor favor, elige otro.', 'danger')
            return redirect(url_for('register'))

        # Crea una instancia de User y establece nombre de usuario y contraseña
        new_user = User(username=username)
        new_user.set_password(password)

        # Agrega el nuevo usuario a la base de datos
        db.session.add(new_user)
        db.session.commit()

        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        
        #enviamos notificación
        message = f"{username} se ha registrado en la web."
        send_notis.send_noti(message, username)

        # Luego, redirige al usuario a la vista de inicio de sesión.
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


## INICIO DE SESION
### Formulario de usuario
class LoginForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[InputRequired()])
    password = PasswordField('Contraseña', validators=[InputRequired()])

### Autenticacion
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            
            #guardamos ip temporalmente
            check = funciones.save_users_ips(current_user.username)
            #enviamos notificación
            message = f"{username} ha iniciado sesión en la web."
            send_notis.send_noti(message, current_user.username)

            return redirect(url_for('home'))
        else:
            flash('Credenciales incorrectas.\nPor favor, inténtalo de nuevo.', 'error')

    return render_template('login.html', form=form)


#FUNCIONES DE USUARIO
## Cargar usuario
@login_manager.user_loader
def load_user(user_id):
    # Esta función debe cargar el objeto de usuario a partir del user_id
    user = User.query.get(user_id)
    return user

## Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

##Has role
def user_has_role(role):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if current_user.is_authenticated and current_user.role == role:
                return fn(*args, **kwargs)
            else:
                flash("No tienes permiso para acceder a esta página.", "danger")
                return redirect(url_for('home'))
        return decorated_view
    return wrapper


#---------  FUNCIONES -----------


#-------------- RUTAS -----------

# Home
@app.route('/')
def home():
    return render_template('index.html')

# Practicas WEB // !!! ACTUALIZAR !!!
@app.route('/get-practicas')
def redirigir_a_practicas():
    #enviamos notificación
    #message = f"{current_user.username} ha accedido a Prácticas"
    #send_notis.send_noti(message. )

    return redirect('/practicas')


# Movies WEB
@app.route('/get-movie-web', methods=['GET'])
@login_required
def redirigir_a_movie_web():
    #enviamos notificación
    message = f"{current_user.username} ha accedido a Movie-Web"
    send_notis.send_noti(message, current_user.username)

    # Realiza la redirección a la URL de Adminer
    return redirect('/movie-web')


# Adminer BBDD
@app.route('/get-adminer', methods=['GET'])
@login_required
def redirigir_a_adminer():
    #enviamos notificación
    message = f"{current_user.username} ha accedido a Adminer."
    send_notis.send_noti(message, current_user.username)

    # Realiza la redirección a la URL de Adminer
    return redirect('/adminer/adminer-4.8.1.php')


# Return PC status
@app.route('/pc-status', methods=['GET', 'POST'])
def show_pc_status():
    #mostramos el estado del pc
    return (funciones.pc_status())


# Encender PC ------------------------------------------------------

##secured pc-on // DESHUSO
#@app.route('/pc-on', methods=['GET', 'POST'])
@user_has_role('admin')
def pc_on():
    comando = 'sudo python /var/www/html/scripts/pc-on.py'
    
    resultado = funciones.ejecutar_script(comando)
    flash (resultado)

    #enviamos notificación
    message = f"{current_user.username} ha encendido el PC desde la web."
    send_notis.send_noti(message, current_user.username)

    return redirect(url_for('home'))


##secured pc-on con esp32 // ACTIVA
@app.route('/pc-on', methods=['GET','POST'])
@user_has_role('admin')
def pc_on_esp32():
    resultado = funciones.pc_on_esp32()
    flash(resultado)

    message = f'{current_user.username} ha encendido el PC desde la web.'
    send_notis.send_noti(message, current_user.username)

    return redirect(url_for('home'))


##unsecured pc-on (automation) // DESHUSO
#@app.route(S_Routes.PC_ON, methods=['GET', 'POST'])
def unsecured_pc_on():
    comando = 'sudo python /var/www/html/scripts/pc-on.py'
    resultado = funciones.ejecutar_script(comando)
    flash (resultado)
    
    #enviamos notificación
    send_notis.send_noti('Se ha encendido el PC remotamente', 'default')

    return redirect(url_for('home'))


##unsecured_pc_on con esp32 // ACTIVA
@app.route(S_Routes.PC_ON, methods=['GET', 'POST'])
def unsecured_pc_on_esp32():
    resultado = funciones.pc_on_esp32()
    flash(resultado)
    
    if (resultado == 'El PC ya está encendido'):
        send_notis.send_noti('Se ha intentado encender el PC, pero ya está encendido.', 'default')
    else:
        send_notis.send_noti('Se ha encendido el PC remotamente', 'default')

    return redirect(url_for('home'))



# PÁGINA CREDENCIALES ------------------------------------------------------

## Gestionar credenciales
@app.route('/gestionar-credenciales', methods=['GET', 'POST'])
@login_required
def gestionar_credenciales():
    #enviamos mensaje
    message = f"{current_user.username} ha accedido a Gestionar Credenciales"
    send_notis.send_noti(message, current_user.username)

    form = CredentialsForm()

    if form.validate_on_submit():
        new_credential = Credentials(
            user_id = current_user.id,
            site = form.site.data,
            user = form.user.data,
            email = form.email.data,
            password = form.password.data,
            description = form.description.data
        )
        
        db.session.add(new_credential)
        db.session.commit()

        flash('La nueva credencial se ha guardado correctamente', 'error')

        return redirect('/gestionar-credenciales')

    return render_template('gestionar-credenciales.html', form=form)


@app.route('/cargar_credenciales', methods=['GET'])
@login_required
def gc_cargar_credenciales():
    #id del usuario que lo solicita
    user_id_session = current_user.id
    
    #obtenemos las credenciales
    user_credentials = db.session.query(Credentials).join(User).filter(Credentials.user_id == user_id_session).order_by(Credentials.site).all()
    
    #las pasamos a diccionarios
    user_credentials_dc = [
        {
            "id": credentials.id, 
            "user_id": credentials.user_id, 
            "site": credentials.site, 
            "user": credentials.user, 
            "email": credentials.email,
            "password": credentials.password,
            "description": credentials.description
        } 
        for credentials in user_credentials
    ]
    
    #devolvemos en json 
    return jsonify(user_credentials_dc)

## Tabla Credenciales
class Credentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    site = db.Column(db.String(255), nullable=False)
    user = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

## Formulario Credenciales
class CredentialsForm(FlaskForm):
    site = StringField('Sitio Web', validators=[InputRequired(), Length(max=255)])
    user = StringField('Usuario', validators=[Length(max=50)])
    email = StringField('Correo Electrónico', validators=[Email(), Length(max=255)])
    password = PasswordField('Contraseña', validators=[InputRequired(), Length(max=255)])
    description = StringField('Descripción', validators=[Length(max=255)])
#------------------------------------------------------------------------------------------

#panel privado
@app.route('/panel-privado')
@login_required
def panel_privado():
    #enviamos notificación
    message = f"{current_user.username} ha accedido a Panel de Control."
    send_notis.send_noti(message, current_user.username)

    return render_template('panel-privado.html')


# PÁGINA ESTADISTICAS ------------------------------------------------

@app.route('/estadisticas')
@login_required
def estadisticas():
    #enviamos notificación
    message = f"{current_user.username} ha accedido a Estadisticas."
    send_notis.send_noti(message, current_user.username)

    return render_template('estadisticas.html')

## Funciones

## Tabla 1 - 
@app.route('/status1_json', methods=['GET'])
def reload_status():
    return jsonify(funciones.datos_status_tabla1())


## Tabla 2 - Escaneo de red
@app.route('/scan2_json', methods=['GET'])
def reload_scan():
    ip_range = '192.168.1.0/24' #IP piso
    #ip_range = '192.168.0.0/24' #IP casa
    return jsonify(ip_nmap_scan.scan_network(ip_range))


# Tabla 10 ultimos accesos
@app.route('/scan3_json', methods=['GET'])
def reload_sql():
    limit = 10
    ip_filter = funciones.get_user_ip(current_user.username)

    return jsonify(funciones.last_access_log_query(limit, ip_filter))


# Tabla resumen 24h
@app.route('/scan4_json', methods=['GET'])
def reload_sql_2():
    limit = 10 

    return jsonify(funciones.most_accesses_by_ip_query(limit))


# Tabla estatus rsp-server
@app.route('/status_t3_json', methods=['GET'])
def reload_status_t3():
    return jsonify(funciones.datos_status_tabla3())


# Tabla estatus pc
@app.route('/status_t4_json', methods=['GET'])
def reload_status_t4():
    return jsonify(funciones.datos_status_tabla4())


## DATOS SENSORES ------------------------------------------------
@app.route('/temp_humd_json', methods=['GET'])
def reload_status_t5():
   return jsonify(funciones.datos_status_tabla5())


@app.route('/control_save_sensor_data_status', methods=['GET'])
def control_save_sensor_data_status():
    if funciones.guardar_datos_sensor == True:
        return 'true'
    else:
        return 'false'


@app.route('/control_save_sensor_data_change_status', methods=['GET'])
@user_has_role('admin')
def control_save_sensor_data_change_status():
    if funciones.guardar_datos_sensor == True:
        funciones.guardar_datos_sensor = False
        return 'false'
    elif funciones.guardar_datos_sensor == False:
        funciones.guardar_datos_sensor = True
        inicio()
        return 'true'

#------------------------------------------------------------------------------

# Manejador de errores para errores internos (código de estado 500)
@app.errorhandler(500)
def internal_server_error(error):
    # Obtenemos las últimas 10 líneas del registro de errores ejecutando el script (lo hacemos asi para evitar errores de permisos)
    comando = 'sudo python /var/www/html/scripts/get-error-log.py'
    
    #Utilizamos la funcion que ya tenemos para ejecutar scripts
    error_log_content = funciones.ejecutar_script(comando) 
    
    #creamos la imagen y la guardamos // NO OPERATIVO por ahora
    ##ruta = '/var/www/html/error_log_image.png'
    ##funciones.text_to_image(error_log_content, ruta)
    
    # Formatea el mensaje de notificación
    message = f'{error}. Error.log:\n{error_log_content}'
    
    #enviamos notificación
    send_notis.send_noti(message, 'default')
    
    return redirect(url_for('home'))

# Ejecuta antes de que llegue la primera request
@app.before_first_request
def inicio():
    #Ejecuta la funcion para guardar los datos del sensor en un hilo independiente
    thread = threading.Thread(target=send_sensor_data_thinkspeak)
    thread.daemon = True
    thread.start()
################################################################
#
#
#
#
if __name__ == '__main__':
    app.run()
