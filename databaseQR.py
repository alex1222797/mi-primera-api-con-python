\import pymysql
import os # Importante para leer las variables de Render

def conectar():
    # Buscamos la URL de Railway en las variables de entorno de Render
    # Si no existe (porque estás en tu PC), usará los datos de localhost
    db_url = os.environ.get('DATABASE_URL')

    if db_url:
        # Si estamos en Render, nos conectamos usando la URL de Railway
        # pymysql puede manejar la conexión mediante la URL o sus partes
        # Aquí te lo pongo desglosado para que sea más seguro:
        conexion = pymysql.connect(
            host="shinkansen.proxy.rlwy.net",
            port=36073,
            user="root",
            passwd="EcNAVDTvwiYvMSBoXpBDzxvpPecsbry",
            database="railway"
        )
    else:
        # Si estás en tu PC (Workbench local), sigue usando esto:
        conexion = pymysql.connect(
            host="localhost",
            user="root",
            passwd="mySQL123", # Tu clave local
            database="SistemaMedicoQR"
        )
    
    return conexion
