from fastapi import FastAPI, Response
from databaseQR import conectar 
import pymysql
from pydantic import BaseModel
from fastapi.responses import HTMLResponse 
from fastapi.middleware.cors import CORSMiddleware
from fpdf import FPDF
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS ---

class DatosVenta(BaseModel):
    to_name: str
    to_email: str
    to_clave: str
    total: str
    metodo_pago: str
    detalle: str

class DatosPaciente(BaseModel):
    nombre: str
    apellido: str
    tipo_sangre: str
    alergias: str
    observaciones: str

class ValidarAcceso(BaseModel):
    email: str
    clave: str

# --- FUNCIÓN AUXILIAR: busca datos completos del paciente por email ---
def _obtener_paciente_por_email(cursor, email: str):
    """
    Busca en ventas el nombre asociado al email,
    luego busca en personas + fichas_medicas por ese nombre.
    Devuelve el dict con todos los datos o None.
    """
    # 1. Verificar que el email existe en ventas
    cursor.execute(
        "SELECT Nombre_Cliente FROM ventas WHERE Email_Cliente = %s LIMIT 1",
        (email,)
    )
    venta = cursor.fetchone()
    if not venta:
        return None

    # 2. Buscar la persona por nombre (ajusta si tienes columna de email en personas)
    nombre_completo = venta['Nombre_Cliente'].split(' ', 1)
    nombre = nombre_completo[0]
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
# LOGIN — ahora devuelve todos los datos del paciente para el Dashboard
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/app/login")
def login_app(datos: ValidarAcceso):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        # 1. Validar credenciales en ventas
        cursor.execute(
            "SELECT * FROM ventas WHERE Email_Cliente = %s AND Clave_Generada = %s",
            (datos.email, datos.clave)
        )
        venta = cursor.fetchone()
        if not venta:
            return {"status": "error", "message": "Acceso Denegado: Datos incorrectos."}

        # 2. Verificar que la clave no esté ya usada
        cursor.execute("SELECT Activo FROM qrs WHERE `Key` = %s", (datos.clave,))
        qr = cursor.fetchone()
        if qr and qr['Activo'] == 1:
            return {"status": "error", "message": "Esta clave ya fue utilizada."}

        # 3. Buscar datos completos del paciente
        paciente = _obtener_paciente_por_email(cursor, datos.email)

        if paciente:
            # Armar el mapa con las mismas keys que usa Flutter
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
            # Si aún no registró su ficha, mandamos datos básicos de la venta
            datos_paciente = {
                "nombre":    venta['Nombre_Cliente'],
                "apellido":  '',
                "correo":    datos.email,
                "tipo_paciente": "Adulto",
            }

        return {
            "status": "ok",
            "paciente": datos_paciente
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if conexion: conexion.close()


# ─────────────────────────────────────────────────────────────────────────────
# ACCESO RÁPIDO BIOMÉTRICO — busca paciente por correo (sin clave)
# Lo usa la app cuando ya tiene la biometría registrada
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
        if conexion: conexion.close()


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRO COMPLETO DEL PACIENTE (sin cambios)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/paciente/completo")
def registrar_todo_el_perfil(data: dict):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor()

        nombre    = data.get('nombre', 'Sin Nombre')
        apellido  = data.get('apellido', 'Sin Apellido')
        tipo      = data.get('tipo_paciente', 'Adulto')
        edad      = data.get('edad', '0')
        dui       = data.get('dui', '00000000-0')
        tel       = data.get('telefono', '0000-0000')
        resp      = data.get('responsable', 'N/A')
        tel_resp  = data.get('telefono_responsable', '0000-0000')

        sql_p = """INSERT INTO personas 
                   (Tipo, Nombre, Apellido, Edad, DUI, Telefono, Responsable_Nombre, Responsable_Telefono) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql_p, (tipo, nombre, apellido, edad, dui, tel, resp, tel_resp))
        id_generado = cursor.lastrowid

        sangre   = data.get('tipo_sangre', 'O+')
        alergias = data.get('alergias', 'Ninguna')
        obs      = f"Med: {data.get('medicamentos', '')} | Enf: {data.get('enfermedades', '')}"

        sql_f = """INSERT INTO fichas_medicas (ID_Persona, Tipo_Sangre, Alergias, Observaciones) 
                   VALUES (%s, %s, %s, %s)"""
        cursor.execute(sql_f, (id_generado, sangre, alergias, obs))

        conexion.commit()
        return {"status": "ok", "id": id_generado}

    except Exception as e:
        if conexion: conexion.rollback()
        print(f"DEBUG: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        if conexion: conexion.close()


# ─────────────────────────────────────────────────────────────────────────────
# RUTAS DE LA WEB (sin cambios)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/web/venta")
def registrar_venta(venta: DatosVenta):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        sql_venta = """INSERT INTO ventas (Nombre_Cliente, Email_Cliente, Clave_Generada, Total, Metodo_Pago, Detalle)
                       VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql_venta, (venta.to_name, venta.to_email, venta.to_clave,
                                   venta.total, venta.metodo_pago, venta.detalle))
        cursor.execute("INSERT IGNORE INTO qrs (`Key`, Activo) VALUES (%s, 0)", (venta.to_clave,))
        conexion.commit()
        conexion.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
        if not d: return "<h1>No encontrado</h1>"
        html_content = """
        <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body{font-family:Arial;background:#f2f2f2;padding:20px;}
            .card{background:white;padding:25px;border-radius:20px;max-width:350px;margin:auto;box-shadow:0 4px 15px rgba(0,0,0,0.2);border-top:10px solid #d32f2f;}
            .title{text-align:center;font-size:24px;font-weight:bold;margin-bottom:20px;color:#d32f2f;}
            .info{margin:15px 0;border-bottom:1px solid #eee;padding-bottom:5px;}
            .label{color:#d32f2f;font-weight:bold;font-size:12px;text-transform:uppercase;display:block;}
            .btn{display:block;padding:15px;margin-top:10px;border-radius:10px;text-decoration:none;color:white;text-align:center;font-weight:bold;background:#d32f2f;}
            .btn-1{display:block;padding:15px;margin-top:10px;border-radius:10px;text-decoration:none;color:white;text-align:center;font-weight:bold;background:blue;}
        </style>
        </head><body><div class="card"><div class="title">🚑 Ficha Médica</div>
        <div class="info"><span class="label">Nombre</span> %s %s</div>
        <div class="info"><span class="label">Sangre</span> %s</div>
        <div class="info"><span class="label">Alergias</span> %s</div>
        <div class="info"><span class="label">Notas</span> %s</div>
        <a class="btn" href="tel:911">📞 EMERGENCIAS (911)</a>
        <a class="btn-1" href="tel:132">📞 SEM (132)</a></div></body></html>
        """ % (d['Nombre'], d['Apellido'], d['Tipo_Sangre'], d['Alergias'], d['Observaciones'])
        return html_content
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"

# ─────────────────────────────────────────────────────────────────────────────
# AGREGAR ESTE ENDPOINT A TU main.py (o donde tengas tu FastAPI)
#
# URL del QR impreso: https://tu-api.onrender.com/qr/ver/{clave}
# Ejemplo:            https://tu-api.onrender.com/qr/ver/MQR001
#
# Cadena de búsqueda:
#   clave → ventas (Clave_Generada) → Email_Cliente
#         → personas (Nombre+Apellido) → fichas_medicas → HTML
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/qr/ver/{clave}", response_class=HTMLResponse)
def ver_ficha_por_clave(clave: str):
    conexion = None
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        # 1. Verificar que el QR existe y está activo
        cursor.execute("SELECT Activo FROM qrs WHERE `Key` = %s", (clave,))
        qr = cursor.fetchone()

        if not qr:
            return _html_error("QR no registrado", "Este código QR no está en el sistema.")

        if qr['Activo'] == 0:
            return _html_inactivo(clave)

        # 2. Buscar el email asociado a esa clave en ventas
        cursor.execute(
            "SELECT Nombre_Cliente, Email_Cliente FROM ventas WHERE Clave_Generada = %s LIMIT 1",
            (clave,)
        )
        venta = cursor.fetchone()
        if not venta:
            return _html_error("Sin datos", "No hay venta asociada a este QR.")

        # 3. Buscar persona + ficha médica por nombre (igual que en _obtener_paciente_por_email)
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
# HELPERS HTML — respuestas visuales del QR
# ─────────────────────────────────────────────────────────────────────────────

def _base_html(titulo: str, cuerpo: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titulo}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
       background:#f0f4f8;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:16px}}
  .card{{background:#fff;border-radius:20px;max-width:380px;width:100%;
         box-shadow:0 8px 30px rgba(0,0,0,.12);overflow:hidden}}
  .header{{background:#c62828;padding:20px;text-align:center;color:#fff}}
  .header h1{{font-size:18px;font-weight:700;margin-top:6px}}
  .header .icon{{font-size:36px}}
  .body{{padding:20px}}
  .row{{display:flex;flex-direction:column;padding:10px 0;border-bottom:1px solid #f0f0f0}}
  .row:last-child{{border-bottom:none}}
  .label{{font-size:11px;font-weight:700;color:#c62828;text-transform:uppercase;letter-spacing:.5px;margin-bottom:3px}}
  .value{{font-size:15px;color:#1a1a1a;font-weight:500}}
  .badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:12px}}
  .badge-nino{{background:#e3f2fd;color:#1565c0}}
  .badge-adulto{{background:#e8f5e9;color:#2e7d32}}
  .badge-mayor{{background:#fff3e0;color:#e65100}}
  .btns{{padding:16px;display:flex;flex-direction:column;gap:10px}}
  .btn{{display:block;padding:14px;border-radius:12px;text-decoration:none;
        color:#fff;text-align:center;font-weight:700;font-size:15px}}
  .btn-911{{background:#c62828}}
  .btn-132{{background:#1565c0}}
  .alert{{padding:20px;text-align:center;color:#555}}
  .alert .big{{font-size:48px;margin-bottom:10px}}
  .alert h2{{font-size:17px;color:#333;margin-bottom:6px}}
  .alert p{{font-size:13px;color:#888}}
</style>
</head><body>{cuerpo}</body></html>"""


def _html_ficha(d: dict) -> str:
    tipo = d.get('Tipo', 'Adulto')
    badge_class = 'badge-nino' if 'ni' in tipo.lower() else ('badge-mayor' if 'mayor' in tipo.lower() else 'badge-adulto')

    responsable = ''
    if d.get('Responsable_Nombre'):
        responsable = f"""
        <div class="row">
          <span class="label">Contacto de emergencia</span>
          <span class="value">{d['Responsable_Nombre']}</span>
        </div>
        <div class="row">
          <span class="label">Teléfono</span>
          <span class="value"><a href="tel:{d['Responsable_Telefono']}" style="color:#c62828">{d['Responsable_Telefono']}</a></span>
        </div>"""

    cuerpo = f"""
    <div class="card">
      <div class="header">
        <div class="icon">🚑</div>
        <h1>Ficha Médica de Emergencia</h1>
      </div>
      <div class="body">
        <span class="badge {badge_class}">{tipo}</span>
        <div class="row">
          <span class="label">Paciente</span>
          <span class="value">{d['Nombre']} {d['Apellido']}</span>
        </div>
        <div class="row">
          <span class="label">Edad</span>
          <span class="value">{d.get('Edad', 'N/A')} años</span>
        </div>
        <div class="row">
          <span class="label">Tipo de sangre</span>
          <span class="value" style="font-size:22px;color:#c62828;font-weight:800">{d['Tipo_Sangre']}</span>
        </div>
        <div class="row">
          <span class="label">Alergias</span>
          <span class="value">{d['Alergias'] or 'Ninguna'}</span>
        </div>
        <div class="row">
          <span class="label">Observaciones</span>
          <span class="value">{d['Observaciones'] or 'Ninguna'}</span>
        </div>
        {responsable}
      </div>
      <div class="btns">
        <a class="btn btn-911" href="tel:911">📞 Emergencias — 911</a>
        <a class="btn btn-132" href="tel:132">🚑 SEM — 132</a>
      </div>
    </div>"""
    return _base_html("Ficha Médica", cuerpo)


def _html_inactivo(clave: str) -> str:
    cuerpo = f"""
    <div class="card">
      <div class="header"><div class="icon">🔒</div><h1>Pulsera no activada</h1></div>
      <div class="body">
        <div class="alert">
          <div class="big">⏳</div>
          <h2>QR pendiente de activación</h2>
          <p>El propietario de esta pulsera aún no ha ingresado sus datos médicos en la aplicación.</p>
        </div>
      </div>
    </div>"""
    return _base_html("Sin activar", cuerpo)


def _html_sin_ficha(nombre: str) -> str:
    cuerpo = f"""
    <div class="card">
      <div class="header"><div class="icon">📋</div><h1>Datos incompletos</h1></div>
      <div class="body">
        <div class="alert">
          <div class="big">⚠️</div>
          <h2>{nombre}</h2>
          <p>El propietario aún no ha completado su ficha médica en la app.</p>
        </div>
      </div>
      <div class="btns">
        <a class="btn btn-911" href="tel:911">📞 Emergencias — 911</a>
        <a class="btn btn-132" href="tel:132">🚑 SEM — 132</a>
      </div>
    </div>"""
    return _base_html("Sin ficha", cuerpo)


def _html_error(titulo: str, detalle: str) -> str:
    cuerpo = f"""
    <div class="card">
      <div class="header"><div class="icon">❌</div><h1>{titulo}</h1></div>
      <div class="body">
        <div class="alert"><p>{detalle}</p></div>
      </div>
    </div>"""
    return _base_html("Error", cuerpo)
