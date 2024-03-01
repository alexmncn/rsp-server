from sqlalchemy import Table, Column, Integer, String, create_engine, MetaData, select, desc
from config import Config

database_uri = Config.SQLALCHEMY_DATABASE_URI

# Crear una conexión al a base de datos
engine = create_engine(database_uri)

# Aquí defines los metadatos de la base de datos
metadata = MetaData()

# Aquí defines la tabla dinámicamente
access_log_table = Table('access_log', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),    
    Column('agent', String(255)),
    Column('bytes_sent', Integer),
    Column('child_pid', Integer),
    Column('cookie', String(255)),
    Column('machine_id', String(25)),
    Column('request_file', String(255)),
    Column('referer', String(255)),
    Column('remote_host', String(50)),
    Column('remote_logname', String(50)),
    Column('remote_user', String(50)),
    Column('request_duration', Integer),
    Column('request_line', String(255)),
    Column('request_method', String(10)),
    Column('request_protocol', String(10)),
    Column('request_time', String(28)),
    Column('request_uri', String(255)),
    Column('request_args', String(255)),
    Column('server_port', Integer),
    Column('ssl_cipher', String(25)),
    Column('ssl_keysize', Integer),
    Column('ssl_maxkeysize', Integer),
    Column('status', Integer),
    Column('time_stamp', Integer),
    Column('virtual_host', String(255)),
    Column('fecha', String(255))
)

def query(selects=None, columns=None, filters=None, group_by=None , order_by=None, limit=None):
    # Crear una consulta base
    if selects:
        query = select(selects)
    else:
        query = select(access_log_table)

    # Aplicar columnas seleccionadas
    if columns:
        query = query.with_only_columns([access_log_table.columns[column] for column in columns])

    # Aplicar filtros
    if filters is not None:    
        query = query.where(filters)

    #Aplicar group
    if group_by is not None:
        query = query.group_by(group_by)

    # Aplicar orden
    if order_by is not None:
        query = query.order_by(order_by)

    # Aplicar límite
    if limit is not None:
        query = query.limit(limit)

    # Ejecutar la consulta
    with engine.connect() as connection:
        result = connection.execute(query)

        return result.fetchall()

