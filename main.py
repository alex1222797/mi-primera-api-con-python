from fastapi import FastAPI, Response
from databaseQR import conectar
import pymysql
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fpdf import FPDF
import io
import random, string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
GMAIL_USER  →  diagnosticomedqr@gmail.com
GMAIL_PASS  →  INFRAMEN2026

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASS = os.getenv("GMAIL_PASS", "")
 
 
def enviar_clave_activacion(nombre: str, email_destino: str, clave: str, qr_key: str) -> bool:
    """
    Envía el correo con la clave de activación al comprador.
    Retorna True si se envió correctamente, False si falló.
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🚑 Tu Pulsera MedQR está lista para activar"
        msg["From"]    = f"MedQR <{GMAIL_USER}>"
        msg["To"]      = email_destino
 
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head><meta charset="UTF-8"></head>
        <body style="margin:0;padding:0;background:#f0f4f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td align="center" style="padding:40px 16px">
              <table width="100%" style="max-width:480px;background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.10)">
 
                <!-- Header -->
                <tr>
                  <td style="background:#c62828;padding:32px 32px 24px;text-align:center">
                    <div style="font-size:48px">🚑</div>
                    <h1 style="color:#ffffff;font-size:22px;font-weight:700;margin:10px 0 4px">¡Tu pulsera está lista!</h1>
                    <p style="color:rgba(255,255,255,.8);font-size:14px;margin:0">MedQR — Ficha Médica Inteligente</p>
                  </td>
                </tr>
 
                <!-- Body -->
                <tr>
                  <td style="padding:32px">
                    <p style="color:#333;font-size:15px;margin:0 0 8px">Hola, <strong>{nombre}</strong> 👋</p>
                    <p style="color:#555;font-size:14px;line-height:1.6;margin:0 0 28px">
                      Tu pulsera inteligente MedQR ha sido registrada. Para activarla e ingresar tus datos médicos, abre la aplicación e ingresa con las siguientes credenciales:
                    </p>
 
                    <!-- Credenciales -->
                    <table width="100%" style="background:#f8f8f8;border-radius:12px;margin-bottom:28px">
                      <tr>
                        <td style="padding:20px 24px">
                          <p style="margin:0 0 14px;font-size:12px;color:#999;text-transform:uppercase;letter-spacing:.5px;font-weight:700">Correo electrónico</p>
                          <p style="margin:0 0 20px;font-size:15px;color:#222;font-weight:600">{email_destino}</p>
 
                          <p style="margin:0 0 10px;font-size:12px;color:#999;text-transform:uppercase;letter-spacing:.5px;font-weight:700">Clave de activación</p>
                          <div style="background:#c62828;border-radius:10px;padding:14px 20px;text-align:center">
                            <span style="color:#ffffff;font-size:28px;font-weight:800;letter-spacing:4px;font-family:monospace">{clave}</span>
                          </div>
                        </td>
                      </tr>
                    </table>
 
                    <!-- Pasos -->
                    <p style="font-size:13px;font-weight:700;color:#333;margin:0 0 12px;text-transform:uppercase;letter-spacing:.4px">Cómo activar</p>
                    <table width="100%">
                      <tr>
                        <td style="padding:6px 0;font-size:14px;color:#555">
                          <span style="background:#c62828;color:#fff;border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;margin-right:10px">1</span>
                          Abre la app MedQR en tu celular
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:6px 0;font-size:14px;color:#555">
                          <span style="background:#c62828;color:#fff;border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;margin-right:10px">2</span>
                          Ingresa tu correo y la clave de arriba
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:6px 0;font-size:14px;color:#555">
                          <span style="background:#c62828;color:#fff;border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;margin-right:10px">3</span>
                          Completa tu ficha médica
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:6px 0;font-size:14px;color:#555">
                          <span style="background:#1565c0;color:#fff;border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;margin-right:10px">✓</span>
                          ¡Tu QR estará activo!
                        </td>
                      </tr>
                    </table>
 
                    <p style="font-size:12px;color:#aaa;margin:28px 0 0;line-height:1.5">
                      Guarda bien tu clave de activación. Si tienes problemas, responde este correo.
                    </p>
                  </td>
                </tr>
 
                <!-- Footer -->
                <tr>
                  <td style="background:#f8f8f8;padding:18px 32px;text-align:center;border-top:1px solid #eee">
                    <p style="font-size:12px;color:#bbb;margin:0">© MedQR — Pulsera Médica Inteligente</p>
                  </td>
                </tr>
 
              </table>
            </td></tr>
          </table>
        </body>
        </html>
        """
 
        msg.attach(MIMEText(html, "html"))
 
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, email_destino, msg.as_string())
 
        return True
 
    except Exception as e:
        print(f"Error enviando correo a {email_destino}: {e}")
        return False
# ─────────────────────────────────────────────────────────────────────────────
# MODELOS
# ─────────────────────────────────────────────────────────────────────────────

class DatosVenta(BaseModel):
     to_name: str
     to_email: str
     total: str
     metodo_pago: str
     detalle: str
     qr_key: str

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
# FUNCIÓN AUXILIAR — busca datos completos del paciente por email
# ─────────────────────────────────────────────────────────────────────────────

def _obtener_paciente_por_email(cursor, email: str):
    cursor.execute(
        "SELECT Nombre_Cliente FROM ventas WHERE Email_Cliente = %s LIMIT 1",
        (email,)
    )
    venta = cursor.fetchone()
    if not venta:
        return None

    nombre_completo = venta['Nombre_Cliente'].split(' ', 1)
    nombre   = nombre_completo[0]
    apellido = nombre_completo[1] if len(nombre_completo) > 1 else ''

    cursor.execute(
        """SELECT p.*, f.Tipo_Sangre, f.Alergias, f.Observaciones, f.ID_Ficha
           FROM personas p
           LEFT JOIN fichas_medicas f ON f.ID_Persona = p.ID_Personas
           WHERE p.Nombre = %s AND p.Apellido = %s
           ORDER BY p.ID_Personas DESC LIMIT 1""",
        (nombre, apellido)
    )
    return cursor.fetchone()


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN — valida credenciales, ENCIENDE el QR y devuelve datos del paciente
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/app/login")
def login_app(datos: ValidarAcceso):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        # 1. Validar correo + clave en ventas
        cursor.execute(
            "SELECT * FROM ventas WHERE Email_Cliente = %s AND Clave_Generada = %s",
            (datos.email, datos.clave)
        )
        venta = cursor.fetchone()
        if not venta:
            return {"status": "error", "message": "Acceso Denegado: Datos incorrectos."}

        # 2. Verificar estado del QR
        cursor.execute("SELECT Activo FROM qrs WHERE `Key` = %s", (datos.clave,))
        qr = cursor.fetchone()

        # 3. ✅ ENCENDER el QR si estaba apagado (primera vez que el usuario entra)
        if qr and qr['Activo'] == 0:
            cursor.execute("UPDATE qrs SET Activo = 1 WHERE `Key` = %s", (datos.clave,))
            conexion.commit()

        # 4. Buscar datos completos del paciente
        paciente = _obtener_paciente_por_email(cursor, datos.email)

        if paciente:
            datos_paciente = {
                "nombre":               paciente.get('Nombre', ''),
                "apellido":             paciente.get('Apellido', ''),
                "edad":                 str(paciente.get('Edad', '')),
                "dui":                  paciente.get('DUI', ''),
                "tipo_paciente":        paciente.get('Tipo', 'Adulto'),
                "responsable":          paciente.get('Responsable_Nombre', ''),
                "telefono_responsable": paciente.get('Responsable_Telefono', ''),
                "tipo_sangre":          paciente.get('Tipo_Sangre', ''),
                "alergias":             paciente.get('Alergias', ''),
                "observaciones":        paciente.get('Observaciones', ''),
                "correo":               datos.email,
                "id_ficha":             str(paciente.get('ID_Ficha', '')),
            }
        else:
            datos_paciente = {
                "nombre":        venta['Nombre_Cliente'],
                "apellido":      '',
                "correo":        datos.email,
                "tipo_paciente": "Adulto",
            }

        return {"status": "ok", "paciente": datos_paciente}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if conexion:
            conexion.close()


# ─────────────────────────────────────────────────────────────────────────────
# ACCESO BIOMÉTRICO — busca paciente por correo (sin clave)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/paciente/correo/{email}")
def obtener_paciente_por_correo(email: str):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        paciente = _obtener_paciente_por_email(cursor, email)
        if not paciente:
            return {"status": "error", "message": "Paciente no encontrado"}

        datos_paciente = {
            "nombre":               paciente.get('Nombre', ''),
            "apellido":             paciente.get('Apellido', ''),
            "edad":                 str(paciente.get('Edad', '')),
            "dui":                  paciente.get('DUI', ''),
            "tipo_paciente":        paciente.get('Tipo', 'Adulto'),
            "responsable":          paciente.get('Responsable_Nombre', ''),
            "telefono_responsable": paciente.get('Responsable_Telefono', ''),
            "tipo_sangre":          paciente.get('Tipo_Sangre', ''),
            "alergias":             paciente.get('Alergias', ''),
            "observaciones":        paciente.get('Observaciones', ''),
            "correo":               email,
            "id_ficha":             str(paciente.get('ID_Ficha', '')),
        }
        return {"status": "ok", "paciente": datos_paciente}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if conexion:
            conexion.close()


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRO COMPLETO DEL PACIENTE
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/paciente/completo")
def registrar_todo_el_perfil(data: dict):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor()

        nombre   = data.get('nombre',    'Sin Nombre')
        apellido = data.get('apellido',  'Sin Apellido')
        tipo     = data.get('tipo_paciente', 'Adulto')
        edad     = data.get('edad',      '0')
        dui      = data.get('dui',       '00000000-0')
        tel      = data.get('telefono',  '0000-0000')
        resp     = data.get('responsable', 'N/A')
        tel_resp = data.get('telefono_responsable', '0000-0000')

        sql_p = """INSERT INTO personas
                   (Tipo, Nombre, Apellido, Edad, DUI, Telefono, Responsable_Nombre, Responsable_Telefono)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql_p, (tipo, nombre, apellido, edad, dui, tel, resp, tel_resp))
        id_persona = cursor.lastrowid

        sangre   = data.get('tipo_sangre', 'O+')
        alergias = data.get('alergias',    'Ninguna')
        obs      = f"Med: {data.get('medicamentos', '')} | Enf: {data.get('enfermedades', '')}"

        sql_f = """INSERT INTO fichas_medicas (ID_Persona, Tipo_Sangre, Alergias, Observaciones)
                   VALUES (%s, %s, %s, %s)"""
        cursor.execute(sql_f, (id_persona, sangre, alergias, obs))

        conexion.commit()
        return {"status": "ok", "id": id_persona}

    except Exception as e:
        if conexion:
            conexion.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        if conexion:
            conexion.close()


# ─────────────────────────────────────────────────────────────────────────────
# VENTA — registra venta y crea el QR en estado OFF
# ─────────────────────────────────────────────────────────────────────────────
def _generar_clave(longitud: int = 8) -> str:
     chars = string.ascii_uppercase + string.digits
     return ''.join(random.choices(chars, k=longitud))
@app.post("/web/venta")
def registrar_venta(venta: DatosVenta):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        sql_venta = """INSERT INTO ventas (Nombre_Cliente, Email_Cliente, Clave_Generada, Total, Metodo_Pago, Detalle)
                       VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql_venta, (venta.to_name, venta.to_email, venta.to_clave,
                                   venta.total, venta.metodo_pago, venta.detalle))
        # Inserta el QR en estado OFF (Activo = 0)
        cursor.execute("INSERT IGNORE INTO qrs (`Key`, Activo) VALUES (%s, 0)", (venta.to_clave,))
        conexion.commit()
        conexion.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# FACTURA PDF
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/web/factura/{clave}")
def descargar_factura(clave: str, nombre: str = "Cliente", total: str = "0.00", items: str = ""):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 22)
        pdf.set_text_color(198, 40, 40)
        pdf.cell(190, 15, "Diagnostico MedQR", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(190, 5, "Comprobante de Compra Electronico", ln=True)
        pdf.ln(10)
        pdf.set_fill_color(198, 40, 40)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(140, 8, " Producto", fill=True)
        pdf.cell(50, 8, " Precio", fill=True, ln=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 10)
        if items:
            for fila in items.split(";"):
                if "|" in fila:
                    p_nom, p_pre = fila.split("|")
                    pdf.cell(140, 8, f" {p_nom}", border="B")
                    pdf.cell(50, 8, f"${p_pre}", border="B", ln=True, align="C")
        pdf.ln(2)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(140, 10, "TOTAL PAGADO: ", align="R")
        pdf.cell(50, 10, f"${total}", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "B", 26)
        pdf.set_text_color(198, 40, 40)
        pdf.cell(190, 15, clave, ln=True, align="C")
        output = pdf.output(dest='S')
        final_payload = bytes(output, 'latin-1') if isinstance(output, str) else bytes(output)
        return Response(
            content=final_payload,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Factura_{clave}.pdf"}
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRO BÁSICO (endpoint original, se mantiene)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/qr/registrar")
def registrar_paciente(datos: DatosPaciente):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO personas (Nombre, Apellido) VALUES (%s, %s)", (datos.nombre, datos.apellido))
        id_p = cursor.lastrowid
        cursor.execute(
            "INSERT INTO fichas_medicas (ID_Persona, Tipo_Sangre, Alergias, Observaciones) VALUES (%s, %s, %s, %s)",
            (id_p, datos.tipo_sangre, datos.alergias, datos.observaciones)
        )
        conexion.commit()
        conexion.close()
        return {"status": "ok", "id_ficha": cursor.lastrowid}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ─────────────────────────────────────────────────────────────────────────────
# Agrega este import al inicio de tu main.py
# ─────────────────────────────────────────────────────────────────────────────
# from email_service import enviar_clave_activacion

# ─────────────────────────────────────────────────────────────────────────────
# Reemplaza tu /web/venta con este
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/web/venta")
def registrar_venta(venta: DatosVenta):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        # 1. Verificar que el QR físico existe y está libre
        cursor.execute("SELECT Activo FROM qrs WHERE `Key` = %s", (venta.qr_key,))
        qr = cursor.fetchone()
        if not qr:
            return {"status": "error", "message": f"El QR {venta.qr_key} no existe."}
        if qr['Activo'] == 1:
            return {"status": "error", "message": f"El QR {venta.qr_key} ya está asignado."}

        # 2. Generar clave única random (reintenta si ya existe)
        clave = None
        for _ in range(10):
            candidata = _generar_clave()
            cursor.execute("SELECT 1 FROM ventas WHERE Clave_Generada = %s", (candidata,))
            if not cursor.fetchone():
                clave = candidata
                break
        if not clave:
            return {"status": "error", "message": "No se pudo generar una clave única."}

        # 3. Guardar la venta con QR_Key y clave separados
        cursor.execute(
            """INSERT INTO ventas
               (Nombre_Cliente, Email_Cliente, Clave_Generada, Total, Metodo_Pago, Detalle, QR_Key)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (venta.to_name, venta.to_email, clave,
             venta.total, venta.metodo_pago, venta.detalle, venta.qr_key)
        )
        conexion.commit()

        # 4. Enviar correo con la clave al comprador
        correo_enviado = enviar_clave_activacion(
            nombre=venta.to_name,
            email_destino=venta.to_email,
            clave=clave,
            qr_key=venta.qr_key
        )

        return {
            "status": "ok",
            "clave_generada": clave,          # por si lo necesitas en el frontend
            "correo_enviado": correo_enviado  # True/False
        }

    except Exception as e:
        if conexion:
            conexion.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        if conexion:
            conexion.close()


# ─────────────────────────────────────────────────────────────────────────────
# Modelo DatosVenta actualizado (reemplaza el tuyo)
# ─────────────────────────────────────────────────────────────────────────────

# class DatosVenta(BaseModel):
#     to_name: str
#     to_email: str
#     total: str
#     metodo_pago: str
#     detalle: str
#     qr_key: str     # ← ID del QR físico de la pulsera (ej: MQR001)
#                     # la clave ya no viene del frontend, se genera aquí


# ─────────────────────────────────────────────────────────────────────────────
# Función generadora de clave (agrégala arriba de /web/venta en main.py)
# ─────────────────────────────────────────────────────────────────────────────

# import random, string
#
# def _generar_clave(longitud: int = 8) -> str:
#     chars = string.ascii_uppercase + string.digits
#     return ''.join(random.choices(chars, k=longitud))
# ─────────────────────────────────────────────────────────────────────────────
# QR LEGACY — por ID_Ficha (se mantiene para compatibilidad)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/qr/ficha/{id}", response_class=HTMLResponse)
def ficha_qr(id: str):
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        sql = """SELECT p.Nombre, p.Apellido, f.Tipo_Sangre, f.Alergias, f.Observaciones
                 FROM fichas_medicas f
                 JOIN personas p ON f.ID_Persona = p.ID_Personas
                 WHERE f.ID_Ficha = %s"""
        cursor.execute(sql, (id,))
        d = cursor.fetchone()
        conexion.close()
        if not d:
            return "<h1>No encontrado</h1>"
        return _html_ficha(d)
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"


# ─────────────────────────────────────────────────────────────────────────────
# ✅ QR NUEVO — por Clave (el que usan las pulseras impresas)
#    URL del QR: https://tu-api.onrender.com/qr/ver/{clave}
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/qr/ver/{clave}", response_class=HTMLResponse)
def ver_ficha_por_clave(clave: str):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        # 1. ¿Existe el QR?
        cursor.execute("SELECT Activo FROM qrs WHERE `Key` = %s", (clave,))
        qr = cursor.fetchone()
        if not qr:
            return _html_error("QR no registrado", "Este código QR no está en el sistema.")

        # 2. ¿Está encendido?
        if qr['Activo'] == 0:
            return _html_inactivo()

        # 3. Buscar email de la venta asociada
        cursor.execute(
            "SELECT Nombre_Cliente, Email_Cliente FROM ventas WHERE Clave_Generada = %s LIMIT 1",
            (clave,)
        )
        venta = cursor.fetchone()
        if not venta:
            return _html_error("Sin datos", "No hay venta asociada a este QR.")

        # 4. Buscar persona + ficha médica
        nombre_completo = venta['Nombre_Cliente'].split(' ', 1)
        nombre   = nombre_completo[0]
        apellido = nombre_completo[1] if len(nombre_completo) > 1 else ''

        cursor.execute(
            """SELECT p.Nombre, p.Apellido, p.Edad, p.Tipo,
                      p.Responsable_Nombre, p.Responsable_Telefono,
                      f.Tipo_Sangre, f.Alergias, f.Observaciones
               FROM personas p
               LEFT JOIN fichas_medicas f ON f.ID_Persona = p.ID_Personas
               WHERE p.Nombre = %s AND p.Apellido = %s
               ORDER BY p.ID_Personas DESC LIMIT 1""",
            (nombre, apellido)
        )
        d = cursor.fetchone()

        if not d or not d.get('Tipo_Sangre'):
            return _html_sin_ficha(venta['Nombre_Cliente'])

        return _html_ficha(d)

    except Exception as e:
        return _html_error("Error del servidor", str(e))
    finally:
        if conexion:
            conexion.close()


# ─────────────────────────────────────────────────────────────────────────────
# HTML HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _base_html(titulo: str, cuerpo: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titulo} — MedQR</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
       background:#f0f4f8;min-height:100vh;display:flex;
       align-items:center;justify-content:center;padding:16px}}
  .card{{background:#fff;border-radius:20px;max-width:390px;width:100%;
         box-shadow:0 8px 30px rgba(0,0,0,.12);overflow:hidden}}
  .header{{background:#c62828;padding:22px 20px;text-align:center;color:#fff}}
  .header .icon{{font-size:38px;display:block;margin-bottom:6px}}
  .header h1{{font-size:18px;font-weight:700;line-height:1.3}}
  .body{{padding:20px}}
  .row{{display:flex;flex-direction:column;padding:11px 0;border-bottom:1px solid #f0f0f0}}
  .row:last-child{{border-bottom:none}}
  .label{{font-size:10px;font-weight:700;color:#c62828;text-transform:uppercase;
          letter-spacing:.6px;margin-bottom:3px}}
  .value{{font-size:15px;color:#111;font-weight:500}}
  .value.sangre{{font-size:24px;font-weight:800;color:#c62828}}
  .badge{{display:inline-block;padding:4px 12px;border-radius:20px;
          font-size:12px;font-weight:600;margin-bottom:14px}}
  .nino{{background:#e3f2fd;color:#1565c0}}
  .adulto{{background:#e8f5e9;color:#2e7d32}}
  .mayor{{background:#fff3e0;color:#e65100}}
  .btns{{padding:16px;display:flex;flex-direction:column;gap:10px}}
  .btn{{display:block;padding:15px;border-radius:12px;text-decoration:none;
        color:#fff;text-align:center;font-weight:700;font-size:15px}}
  .r{{background:#c62828}} .b{{background:#1565c0}}
  .alert{{padding:28px 20px;text-align:center}}
  .alert .ico{{font-size:50px;display:block;margin-bottom:12px}}
  .alert h2{{font-size:17px;color:#222;margin-bottom:8px;font-weight:600}}
  .alert p{{font-size:13px;color:#888;line-height:1.5}}
</style></head>
<body>{cuerpo}</body></html>"""


def _html_ficha(d: dict) -> str:
    tipo = d.get('Tipo', 'Adulto') or 'Adulto'
    if 'ni' in tipo.lower():
        badge = f'<span class="badge nino">👶 Niño/a</span>'
    elif 'mayor' in tipo.lower():
        badge = f'<span class="badge mayor">👴 Adulto Mayor</span>'
    else:
        badge = f'<span class="badge adulto">🧑 Adulto</span>'

    responsable_html = ''
    if d.get('Responsable_Nombre'):
        responsable_html = f"""
        <div class="row">
          <span class="label">Contacto de emergencia</span>
          <span class="value">{d['Responsable_Nombre']}</span>
        </div>
        <div class="row">
          <span class="label">Teléfono</span>
          <span class="value">
            <a href="tel:{d['Responsable_Telefono']}" style="color:#c62828;text-decoration:none">
              {d['Responsable_Telefono']}
            </a>
          </span>
        </div>"""

    cuerpo = f"""
    <div class="card">
      <div class="header">
        <span class="icon">🚑</span>
        <h1>Ficha Médica de Emergencia</h1>
      </div>
      <div class="body">
        {badge}
        <div class="row">
          <span class="label">Paciente</span>
          <span class="value">{d.get('Nombre','')} {d.get('Apellido','')}</span>
        </div>
        <div class="row">
          <span class="label">Edad</span>
          <span class="value">{d.get('Edad', 'N/A')} años</span>
        </div>
        <div class="row">
          <span class="label">Tipo de sangre</span>
          <span class="value sangre">{d.get('Tipo_Sangre','')}</span>
        </div>
        <div class="row">
          <span class="label">Alergias</span>
          <span class="value">{d.get('Alergias','Ninguna') or 'Ninguna'}</span>
        </div>
        <div class="row">
          <span class="label">Observaciones</span>
          <span class="value">{d.get('Observaciones','Ninguna') or 'Ninguna'}</span>
        </div>
        {responsable_html}
      </div>
      <div class="btns">
        <a class="btn r" href="tel:911">📞 Emergencias — 911</a>
        <a class="btn b" href="tel:132">🚑 SEM — 132</a>
      </div>
    </div>"""
    return _base_html("Ficha Médica", cuerpo)


def _html_inactivo() -> str:
    cuerpo = """
    <div class="card">
      <div class="header"><span class="icon">🔒</span><h1>Pulsera no activada</h1></div>
      <div class="body">
        <div class="alert">
          <span class="ico">⏳</span>
          <h2>QR pendiente de activación</h2>
          <p>El propietario aún no ha ingresado sus credenciales en la aplicación MedQR.</p>
        </div>
      </div>
      <div class="btns">
        <a class="btn r" href="tel:911">📞 Emergencias — 911</a>
        <a class="btn b" href="tel:132">🚑 SEM — 132</a>
      </div>
    </div>"""
    return _base_html("Sin activar", cuerpo)


def _html_sin_ficha(nombre: str) -> str:
    cuerpo = f"""
    <div class="card">
      <div class="header"><span class="icon">📋</span><h1>Datos incompletos</h1></div>
      <div class="body">
        <div class="alert">
          <span class="ico">⚠️</span>
          <h2>{nombre}</h2>
          <p>El propietario aún no completó su ficha médica en la app MedQR.</p>
        </div>
      </div>
      <div class="btns">
        <a class="btn r" href="tel:911">📞 Emergencias — 911</a>
        <a class="btn b" href="tel:132">🚑 SEM — 132</a>
      </div>
    </div>"""
    return _base_html("Sin ficha", cuerpo)


def _html_error(titulo: str, detalle: str) -> str:
    cuerpo = f"""
    <div class="card">
      <div class="header"><span class="icon">❌</span><h1>{titulo}</h1></div>
      <div class="body">
        <div class="alert"><span class="ico">🔍</span><p>{detalle}</p></div>
      </div>
    </div>"""
    return _base_html("Error", cuerpo)
