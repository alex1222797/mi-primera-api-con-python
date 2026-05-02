from fastapi import FastAPI, HTTPException
from databaseQR import conectar 
import pymysql
from pydantic import BaseModel
from fastapi.responses import HTMLResponse 

app = FastAPI()

# --- MODELO PARA RECIBIR DATOS DESDE FLUTTER ---
class DatosPaciente(BaseModel):
    nombre: str
    apellido: str
    tipo_sangre: str
    alergias: str
    observaciones: str

# --- 1. ENDPOINT PARA REGISTRAR DESDE FLUTTER ---
@app.post("/qr/registrar")
def registrar_paciente(datos: DatosPaciente):
    try:
        conexion = conectar()
        cursor = conexion.cursor()

        # Insertar en la tabla 'personas'
        sql_persona = "INSERT INTO personas (Nombre, Apellido) VALUES (%s, %s)"
        cursor.execute(sql_persona, (datos.nombre, datos.apellido))
        id_persona = cursor.lastrowid # Recuperamos el ID generado automáticamente

        # Insertar en la tabla 'fichas_medicas' vinculando con id_persona
        sql_ficha = """
            INSERT INTO fichas_medicas (ID_Persona, Tipo_Sangre, Alergias, Observaciones) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql_ficha, (id_persona, datos.tipo_sangre, datos.alergias, datos.observaciones))
        id_ficha = cursor.lastrowid # Este es el ID que usará el código QR

        conexion.commit()
        conexion.close()

        return {
            "status": "ok", 
            "id_ficha": id_ficha, 
            "message": "Paciente guardado con éxito"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 2. ENDPOINT PARA VER LA FICHA (LECTURA DEL QR) ---
@app.get("/qr/ficha/{id}", response_class=HTMLResponse)
def ficha_qr(id: str):
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        
        # Consulta SQL con JOIN para unir personas y fichas
        sql = """
            SELECT 
                p.Nombre,
                p.Apellido,
                f.Tipo_Sangre,
                f.Alergias,
                f.Observaciones
            FROM fichas_medicas f
            JOIN personas p ON f.ID_Persona = p.ID_Personas
            WHERE f.ID_Ficha = %s
        """
        
        cursor.execute(sql, (id,))
        data = cursor.fetchone()
        conexion.close()

        if not data:
            return f"""
            <html>
                <body style="font-family:Arial; text-align:center; padding-top:50px;">
                    <h1>⚠️ No se encontró la ficha</h1>
                    <p>El ID {id} no existe en la base de datos.</p>
                </body>
            </html>
            """

        # Retornar el HTML con los datos
        html = f"""
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
        return html

    except Exception as e:
        return f"<h1>Error en el servidor</h1><p>{str(e)}</p>"
