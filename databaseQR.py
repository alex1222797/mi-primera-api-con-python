import pymysql

def conectar(): #funcion para conectar
    conexion = pymysql.connect(
        host="localhost", #servidor local
        user="root", #usuario db
        passwd="mySQL123", #contrasña
        database="SistemaMedicoQR" #db
    )
    return conexion