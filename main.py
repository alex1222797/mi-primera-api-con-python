from fastapi import FastAPI
from databaseQR import conectar 
import pymysql
from pydantic import BaseModel
from fastapi.responses import HTMLResponse 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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
        sql = """INSERT INTO ventas (Nombre_Cliente, Email_Cliente, Clave_Generada, Total, Metodo_Pago) 
                 VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (venta.to_name, venta.to_email, venta.to_clave, venta.total, venta.metodo_pago))
        cursor.execute("INSERT IGNORE INTO qrs (`Key`, Activo) VALUES (%s, 0)", (venta.to_clave,))
        conexion.commit()
        conexion.close()
        return {"status": "ok"}
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
        cursor.execute("INSERT INTO personas (Nombre, Apellido) VALUES (%s, %s)", (datos.nombre, datos.apellido))
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
        sql = """SELECT p.Nombre, p.Apellido, f.Tipo_Sangre, f.Alergias, f.Observaciones 
                 FROM fichas_medicas f JOIN personas p ON f.ID_Persona = p.ID_Personas WHERE f.ID_Ficha = %s"""
        cursor.execute(sql, (id,))
        d = cursor.fetchone()
        conexion.close()
        if not d: return "<h1>No encontrado</h1>"
        return f"""
        <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>body{{font-family:Arial;background:#f2f2f2;padding:20px;}}
        .card{{background:white;padding:25px;border-radius:20px;max-width:350px;margin:auto;box-shadow:0 4px 15px rgba(0,0,0,0.2);border-top:10px solid #ff4b2b;}}
        .title{{text-align:center;font-size:24px;font-weight:bold;margin-bottom:20px;}}
        .info{{margin:15px 0;border-bottom:1px solid #eee;padding-bottom:5px;}}
        .label{{color:#ff4b2b;font-weight:bold;font-size:12px;text-transform:uppercase;display:block;}}
        .btn{{display:block;padding:15px;margin-top:10px;border-radius:10px;text-decoration:none;color:white;text-align:center;font-weight:bold;background:#d32f2f;}}
         .btn-1{{display:block;padding:15px;margin-top:10px;border-radius:10px;text-decoration:none;color:white;text-align:center;font-weight:bold;background:blue;}}</style>
        </head><body><div class="card"><div class="title">🚑 Ficha Médica</div>
        <div class="info"><span class="label">Nombre</span> {d['Nombre']} {d['Apellido']}</div>
        <div class="info"><span class="label">Sangre</span> {d['Tipo_Sangre']}</div>
        <div class="info"><span class="label">Alergias</span> {d['Alergias']}</div>
        <div class="info"><span class="label">Notas</span> {d['Observaciones']}</div>
        <a class="btn" href="tel:911">📞 EMERGENCIAS (911)</a>
        <a class="btn-1" href="tel:132">📞 SEM (132)</a></div></body></html>"""
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"
