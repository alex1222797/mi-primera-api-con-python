from fastapi import FastAPI
from databaseQR import conectar 
import pymysql
from pydantic import BaseModel
from fastapi.responses import HTMLResponse 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- ESTA PARTE ES LA QUE ARREGLA EL ERROR DE CORS ---
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
        sql_venta = """
            INSERT INTO ventas (Nombre_Cliente, Email_Cliente, Clave_Generada, Total, Metodo_Pago)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql_venta, (venta.to_name, venta.to_email, venta.to_clave, venta.total, venta.metodo_pago))
        
        sql_qr = "INSERT IGNORE INTO qrs (`Key`, Activo) VALUES (%s, 0)"
        cursor.execute(sql_qr, (venta.to_clave,))

        conexion.commit()
        conexion.close()
        return {"status": "ok", "message": "Venta guardada"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
        sql_persona = "INSERT INTO personas (Nombre, Apellido) VALUES (%s, %s)"
        cursor.execute(sql_persona, (datos.nombre, datos.apellido))
        id_persona = cursor.lastrowid 

        sql_ficha = """
            INSERT INTO fichas_medicas (ID_Persona, Tipo_Sangre, Alergias, Observaciones) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql_ficha, (id_persona, datos.tipo_sangre, datos.alergias, datos.observaciones))
        id_ficha = cursor.lastrowid 

        conexion.commit()
        conexion.close()
        return {"status": "ok", "id_ficha": id_ficha}
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

        if not data: return "<h1>No existe</h1>"

        return f"<html><body style='font-family:Arial; padding:20px;'><h1>🚑 Ficha Médica</h1><p><b>Paciente:</b> {data['Nombre']} {data['Apellido']}</p><p><b>Sangre:</b> {data['Tipo_Sangre']}</p><p><b>Alergias:</b> {data['Alergias']}</p></body></html>"
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"
