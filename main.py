from fastapi import FastAPI, Response
from databaseQR import conectar
import pymysql
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fpdf import FPDF
import io
import random
import string
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables de Entorno (Configúralas en el dashboard de Render)
GMAIL_USER = os.getenv("GMAIL_USER", "diagnosticomedqr@gmail.com")
GMAIL_PASS = os.getenv("GMAIL_PASS", "INFRAMEN2026")

# ─────────────────────────────────────────────────────────────────────────────
# MODELOS DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

class DatosVenta(BaseModel):
    to_name: str
    to_email: str
    total: str
    metodo_pago: str
    detalle: str
    qr_key: str  # ID del QR físico (ej: MQR001)

class DatosPaciente(BaseModel):
    nombre: str
    apellido: str
    tipo_sangre: str
    alergias: str
    observaciones: str

class ValidarAcceso(BaseModel):
    email: str
    clave: str

# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────────────────────────────────────

def _generar_clave(longitud: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=longitud))

def enviar_clave_activacion(nombre: str, email_destino: str, clave: str, qr_key: str) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🚑 Tu Pulsera MedQR está lista para activar"
        msg["From"] = f"MedQR <{GMAIL_USER}>"
        msg["To"] = email_destino

        html = f"""
        <html>
        <body style="font-family:sans-serif; background:#f0f4f8; padding:20px;">
            <div style="max-width:500px; background:#fff; margin:auto; border-radius:15px; overflow:hidden; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
                <div style="background:#c62828; color:#fff; padding:30px; text-align:center;">
                    <h2>¡Hola {nombre}!</h2>
                    <p>Tu pulsera {qr_key} ha sido registrada.</p>
                </div>
                <div style="padding:30px; text-align:center;">
                    <p>Usa esta clave en la app para activar tu perfil:</p>
                    <h1 style="background:#f0f0f0; padding:10px; letter-spacing:5px;">{clave}</h1>
                    <p style="font-size:12px; color:#666;">No compartas esta clave con nadie.</p>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, email_destino, msg.as_string())
        return True
    except Exception as e:
        print(f"Error mail: {e}")
        return False

def _obtener_paciente_por_email(cursor, email: str):
    cursor.execute("SELECT Nombre_Cliente FROM ventas WHERE Email_Cliente = %s LIMIT 1", (email,))
    venta = cursor.fetchone()
    if not venta: return None

    partes = venta['Nombre_Cliente'].split(' ', 1)
    nom = partes[0]
    ape = partes[1] if len(partes) > 1 else ''

    cursor.execute("""
        SELECT p.*, f.Tipo_Sangre, f.Alergias, f.Observaciones, f.ID_Ficha
        FROM personas p
        LEFT JOIN fichas_medicas f ON f.ID_Persona = p.ID_Personas
        WHERE p.Nombre = %s AND p.Apellido = %s
        ORDER BY p.ID_Personas DESC LIMIT 1
    """, (nom, ape))
    return cursor.fetchone()

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS DE VENTA Y APP
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/web/venta")
def registrar_venta(venta: DatosVenta):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        # 1. Verificar QR
        cursor.execute("SELECT Activo FROM qrs WHERE `Key` = %s", (venta.qr_key,))
        qr = cursor.fetchone()
        if not qr: return {"status": "error", "message": "QR no existe"}
        if qr['Activo'] == 1: return {"status": "error", "message": "QR ya ocupado"}

        # 2. Generar clave
        clave = _generar_clave()

        # 3. Guardar Venta
        cursor.execute("""
            INSERT INTO ventas (Nombre_Cliente, Email_Cliente, Clave_Generada, Total, Metodo_Pago, Detalle, QR_Key)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (venta.to_name, venta.to_email, clave, venta.total, venta.metodo_pago, venta.detalle, venta.qr_key))
        
        conexion.commit()
        enviado = enviar_clave_activacion(venta.to_name, venta.to_email, clave, venta.qr_key)
        
        return {"status": "ok", "clave": clave, "correo": enviado}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if conexion: conexion.close()

@app.post("/app/login")
def login_app(datos: ValidarAcceso):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT * FROM ventas WHERE Email_Cliente = %s AND Clave_Generada = %s", (datos.email, datos.clave))
        venta = cursor.fetchone()
        if not venta: return {"status": "error", "message": "Datos incorrectos"}

        # Activar QR si es primera vez
        cursor.execute("UPDATE qrs SET Activo = 1 WHERE `Key` = %s", (venta['QR_Key'],))
        conexion.commit()

        paciente = _obtener_paciente_por_email(cursor, datos.email)
        return {"status": "ok", "paciente": paciente or {"nombre": venta['Nombre_Cliente']}}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if conexion: conexion.close()

# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZACIÓN DE QR (HTML)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/qr/ver/{clave}", response_class=HTMLResponse)
def ver_ficha_por_clave(clave: str):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT Activo FROM qrs WHERE `Key` = %s", (clave,))
        qr = cursor.fetchone()
        if not qr: return "<h1>QR no encontrado</h1>"
        if qr['Activo'] == 0: return "<h1>Pulsera no activada</h1>"

        cursor.execute("SELECT Nombre_Cliente FROM ventas WHERE Clave_Generada = %s", (clave,))
        v = cursor.fetchone()
        paciente = _obtener_paciente_por_email(cursor, v['Email_Cliente'])
        
        if not paciente: return f"<h1>Ficha incompleta de {v['Nombre_Cliente']}</h1>"
        
        return _html_ficha(paciente)
    except Exception as e:
        return f"<h1>Error: {e}</h1>"
    finally:
        if conexion: conexion.close()

def _html_ficha(d: dict) -> str:
    # Versión simplificada del HTML para el ejemplo
    return f"""
    <html>
    <body style="font-family:sans-serif; text-align:center; padding:50px; background:#f0f0f0;">
        <div style="background:#fff; padding:20px; border-radius:20px; box-shadow:0 5px 15px rgba(0,0,0,0.1);">
            <h1 style="color:#c62828;">🚑 FICHA MÉDICA</h1>
            <hr>
            <p><strong>Paciente:</strong> {d.get('Nombre')} {d.get('Apellido')}</p>
            <p><strong>Sangre:</strong> <span style="font-size:2em; color:#c62828;">{d.get('Tipo_Sangre')}</span></p>
            <p><strong>Alergias:</strong> {d.get('Alergias')}</p>
            <p><strong>Notas:</strong> {d.get('Observaciones')}</p>
            <br>
            <a href="tel:911" style="background:#c62828; color:#fff; padding:15px; text-decoration:none; border-radius:10px;">LLAMAR EMERGENCIAS</a>
        </div>
    </body>
    </html>
    """

# ─────────────────────────────────────────────────────────────────────────────
# FACTURA Y REGISTRO PACIENTE
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/paciente/completo")
def registrar_todo_el_perfil(data: dict):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        sql_p = "INSERT INTO personas (Tipo, Nombre, Apellido, Edad, DUI) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql_p, (data.get('tipo'), data.get('nombre'), data.get('apellido'), data.get('edad'), data.get('dui')))
        id_p = cursor.lastrowid
        
        sql_f = "INSERT INTO fichas_medicas (ID_Persona, Tipo_Sangre, Alergias, Observaciones) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_f, (id_p, data.get('tipo_sangre'), data.get('alergias'), data.get('observaciones')))
        
        conexion.commit()
        return {"status": "ok", "id": id_p}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if conexion: conexion.close()

@app.get("/web/factura/{clave}")
def descargar_factura(clave: str, nombre: str = "Cliente", total: str = "0.00"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(40, 10, f"Factura MedQR - {clave}")
    pdf.ln(20)
    pdf.set_font("Arial", "", 12)
    pdf.cell(40, 10, f"Cliente: {nombre}")
    pdf.ln(10)
    pdf.cell(40, 10, f"Total Pagado: ${total}")
    
    output = pdf.output(dest='S').encode('latin-1')
    return Response(content=output, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Factura_{clave}.pdf"})
