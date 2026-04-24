import pymysql
import os
from urllib.parse import urlparse

def conectar():
    # Intentar leer la URL de la variable de Render
    url_str = os.environ.get('DATABASE_URL')
    
    if url_str:
        # Esto separa automáticamente usuario, password, host y puerto
        url = urlparse(url_str)
        return pymysql.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            passwd=url.password,
            database=url.path[1:], # Quita el '/' del nombre de la base
            connect_timeout=10
        )
    else:
        # Conexión local para tu PC
        return pymysql.connect(
            host="localhost",
            user="root",
            passwd="mySQL123",
            database="SistemaMedicoQR"
        )
