from fastapi import FastAPI, Response
from databaseQR import conectar 
import pymysql
from pydantic import BaseModel
from fastapi.responses import HTMLResponse 
from fastapi.middleware.cors import CORSMiddleware
from fpdf import FPDF
import io

app = FastAPI()

# CONFIGURACIÓN DE CORS
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

# --- RUTAS DE LA WEB ---

@app.get("/web/factura/{clave}")
def descargar_factura(clave: str):
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT * FROM ventas WHERE Clave_Generada = %s"
        cursor.execute(sql, (clave,))
        v = cursor.fetchone()
        conexion.close()

        if not v:
            return {"status": "error", "message": "Venta no encontrada"}

        # Crear el PDF con el formato solicitado 
        pdf = FPDF()
        pdf.add_page()
        
        # --- ENCABEZADO PROFESIONAL ---
        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, "DiagnosticoMedQR", ln=True, align="L") # [cite: 1]
        pdf.set_font("Arial", "", 12)
        pdf.cell(190, 8, "Comprobante de Compra Electronico", ln=True, align="L") # [cite: 2]
        pdf.ln(5)
        pdf.line(10, 35, 200, 35)
        
        # --- DATOS DEL CLIENTE ---
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "DATOS DEL CLIENTE", ln=True) # [cite: 3]
        pdf.set_font("Arial", "", 11)
        pdf.cell(190, 7, f"Nombre: {v['Nombre_Cliente']}", ln=True) # [cite: 4]
        pdf.cell(190, 7, f"Email: {v['Email_Cliente']}", ln=True) # [cite: 5]
        pdf.cell(190, 7, f"Fecha: 5/8/2026", ln=True) # [cite: 6]
        
        # --- TABLA DE PRODUCTOS ---
        pdf.ln(10)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(140, 10, " Producto", border=1, fill=True) # [cite: 7]
        pdf.cell(50, 10, " Precio", border=1, fill=True, ln=True) # [cite: 7]
        
        pdf.set_font("Arial", "", 11)
        # Limpieza básica del detalle para evitar errores de caracteres
        detalle_texto = v['Detalle'].replace('|', '-').strip()
        pdf.cell(140, 10, f" {detalle_texto}", border=1)
        pdf.cell(50, 10, f" ${v['Total']}.00", border=1, ln=True) # [cite: 7]
        
        pdf.set_font("Arial", "B", 11)
        pdf.cell(140, 10, " TOTAL PAGADO:", border=1, align="R")
        pdf.cell(50, 10, f" ${v['Total']}.00", border=1, ln=True) # [cite: 7]
        
        # --- CLAVE DE ACTIVACIÓN ---
        pdf.ln(15)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "TU CLAVE DE ACTIVACION PARA LA APP:", ln=True, align="C") # [cite: 8]
        pdf.set_font("Arial", "B", 24)
        pdf.set_text_color(198, 40, 40) # Color rojo corporativo
        pdf.cell(190, 20, v['Clave_Generada'], ln=True, align="C") # [cite: 9]
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(190, 8, "Use esta clave en nuestra App oficial para configurar su pulsera medica.", align="C") # [cite: 10]

        # --- GENERACIÓN FINAL ---
        # Aseguramos que se genere como bytes sin referencias externas
        resultado_pdf = pdf.output() 
        
        return Response(
            content=resultado_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Factura_{clave}.pdf"}
        )
    except Exception as e:
        # Esto te dirá exactamente qué falla si ocurre algo nuevo
        return {"status": "error", "message": str(e)}
# --- RUTAS RESTANTES (LOGIN Y REGISTRO) ---

class ValidarAcceso(BaseModel):
    email: str
    clave: str

@app.post("/app/login")
def login_app(datos: ValidarAcceso):
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT * FROM ventas WHERE Email_Cliente = %s AND Clave_Generada = %s"
        cursor.execute(sql, (datos.email, datos.clave))
        venta = cursor.fetchone()
        
        if not venta:
            return {"status": "error", "message": "Acceso Denegado: Datos incorrectos."}
        
        sql_qr = "SELECT Activo FROM qrs WHERE `Key` = %s"
        cursor.execute(sql_qr, (datos.clave,))
        qr = cursor.fetchone()
        
        if qr and qr['Activo'] == 1:
            return {"status": "error", "message": "Esta clave ya fue utilizada."}
            
        return {"status": "success", "message": "Bienvenido", "cliente": venta['Nombre_Cliente']}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if 'conexion' in locals(): conexion.close()

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
        return f"<html>...</html>" # (Aquí va tu HTML de la ficha médica)
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"

# --- RUTAS DEL APP / QR ---

@app.post("/app/login")
def login_app(datos: ValidarAcceso):
    try:
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        
        sql = "SELECT * FROM ventas WHERE Email_Cliente = %s AND Clave_Generada = %s"
        cursor.execute(sql, (datos.email, datos.clave))
        venta = cursor.fetchone()
        
        if not venta:
            return {"status": "error", "message": "Acceso Denegado: Datos incorrectos."}
        
        sql_qr = "SELECT Activo FROM qrs WHERE `Key` = %s"
        cursor.execute(sql_qr, (datos.clave,))
        qr = cursor.fetchone()
        
        if qr and qr['Activo'] == 1:
            return {"status": "error", "message": "Esta clave ya fue utilizada."}
            
        return {"status": "success", "message": "Bienvenido", "cliente": venta['Nombre_Cliente']}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if 'conexion' in locals(): conexion.close()

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
        .card{{background:white;padding:25px;border-radius:20px;max-width:350px;margin:auto;box-shadow:0 4px 15px rgba(0,0,0,0.2);border-top:10px solid #d32f2f;}}
        .title{{text-align:center;font-size:24px;font-weight:bold;margin-bottom:20px;color:#d32f2f;}}
        .info{{margin:15px 0;border-bottom:1px solid #eee;padding-bottom:5px;}}
        .label{{color:#d32f2f;font-weight:bold;font-size:12px;text-transform:uppercase;display:block;}}
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
