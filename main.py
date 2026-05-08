from fastapi import FastAPI
from databaseQR import conectar 
import pymysql
from pydantic import BaseModel
from fastapi.responses import HTMLResponse 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Esto permite que tu página local hable con Render sin bloqueos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DatosVenta(BaseModel):
    to_name: str
    to_email: str
    to_clave: str
    total: str
    metodo_pago: str

@app.post("/web/venta")
def registrar_venta(venta: DatosVenta):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        sql = """
            INSERT INTO ventas (Nombre_Cliente, Email_Cliente, Clave_Generada, Total, Metodo_Pago)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (venta.to_name, venta.to_email, venta.to_clave, venta.total, venta.metodo_pago))
        
        sql_qr = "INSERT IGNORE INTO qrs (`Key`, Activo) VALUES (%s, 0)"
        cursor.execute(sql_qr, (venta.to_clave,))

        conexion.commit()
        conexion.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ENDPOINTS PARA FLUTTER ---
class DatosPaciente(BaseModel):
    nombre: str
    apellido: str
    tipo_sangre: str
    alergias: str
    observaciones: str

@app.post("/qr/registrar")
def registrar_paciente(datos: DatosPaciente):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        sql_p = "INSERT INTO personas (Nombre, Apellido) VALUES (%s, %s)"
        cursor.execute(sql_p, (datos.nombre, datos.apellido))
        id_p = cursor.lastrowid
        sql_f = "INSERT INTO fichas_medicas (ID_Persona, Tipo_Sangre, Alergias, Observaciones) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_f, (id_p, datos.tipo_sangre, datos.alergias, datos.observaciones))
        id_f = cursor.lastrowid
        conexion.commit()
        conexion.close()
        return {"status": "ok", "id_ficha": id_f}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/qr/ficha/{id}", response_class=HTMLResponse)
def ficha_qr(id: str):
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT p.Nombre, p.Apellido, f.Tipo_Sangre, f.Alergias, f.Observaciones FROM fichas_medicas f JOIN personas p ON f.ID_Persona = p.ID_Personas WHERE f.ID_Ficha = %s"
        cursor.execute(sql, (id,))
        data = cursor.fetchone()
        conexion.close()
        if not data: return "<h1>No encontrado</h1>"
        return f"<html><body><h1>🚑 Ficha Médica</h1><p>{data['Nombre']} {data['Apellido']}</p></body></html>"
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"
