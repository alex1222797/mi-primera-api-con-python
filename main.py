from fastapi import FastAPI, HTTPException
from databaseQR import conectar 
import pymysql
from pydantic import BaseModel
from fastapi.responses import HTMLResponse 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CONFIGURACIÓN CORS: Esto es lo que permite que tu Web hable con Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DATOS ---
class DatosVenta(BaseModel):
    to_name: str
    to_email: str
    to_clave: str
    total: str
    metodo_pago: str

class DatosPaciente(BaseModel):
    nombre: str
    apellido: str
    tipo_sangre: str
    alergias: str
    observaciones: str

# --- ENDPOINT 1: DESDE EL SITIO WEB ---
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
        return {"status": "ok", "message": "Venta sincronizada"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ENDPOINT 2: DESDE FLUTTER (REGISTRO) ---
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

# --- ENDPOINT 3: LECTURA DEL QR (LA FICHA MÉDICA PRO) ---
@app.get("/qr/ficha/{id}", response_class=HTMLResponse)
def ficha_qr(id: str):
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        
        sql = """
            SELECT p.Nombre, p.Apellido, f.Tipo_Sangre, f.Alergias, f.Observaciones
            FROM fichas_medicas f
            JOIN personas p ON f.ID_Persona = p.ID_Personas
            WHERE f.ID_Ficha = %s
        """
        cursor.execute(sql, (id,))
        data = cursor.fetchone()
        conexion.close()

        if not data:
            return "<html><body><h1>Ficha no encontrada</h1></body></html>"

        return f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f2f2f2; margin: 0; padding: 20px; }}
                .card {{ background: white; padding: 25px; border-radius: 20px; max-width: 350px; margin: auto; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); border-top: 10px solid #ff4b2b; }}
                .title {{ text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; color: #333; }}
                .info {{ margin: 15px 0; font-size: 16px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                .label {{ color: #ff4b2b; font-weight: bold; display: block; font-size: 12px; text-transform: uppercase; }}
                .emergency {{ margin-top: 25px; display: flex; flex-direction: column; gap: 12px; }}
                .btn {{ padding: 15px; border-radius: 10px; text-decoration: none; color: white; text-align: center; font-weight: bold; font-size: 16px; }}
                .btn911 {{ background: #d32f2f; }}
                .btn132 {{ background: #1976d2; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="title">🚑 Ficha Médica</div>
                <div class="info"><span class="label">Nombre completo</span> {data['Nombre']} {data['Apellido']}</div>
                <div class="info"><span class="label">Tipo de sangre</span> {data['Tipo_Sangre']}</div>
                <div class="info"><span class="label">Alergias</span> {data['Alergias']}</div>
                <div class="info"><span class="label">Observaciones</span> {data['Observaciones']}</div>
                <div class="emergency">
                    <a class="btn btn911" href="tel:911">📞 EMERGENCIAS (911)</a>
                    <a class="btn btn132" href="tel:132">📞 SEM (132)</a>
                </div>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"
