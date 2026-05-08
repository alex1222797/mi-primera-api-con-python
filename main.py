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

@app.post("/web/venta")
def registrar_venta(venta: DatosVenta):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        sql_venta = """
        INSERT INTO ventas (Nombre_Cliente, Email_Cliente, Clave_Generada, Total, Metodo_Pago, Detalle)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
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
        
        # --- ENCABEZADO ESTILO MEDQR ---
        pdf.set_font("Arial", "B", 22)
        pdf.set_text_color(198, 40, 40) 
        pdf.cell(190, 15, "Diagnostico MedQR", ln=True)
        
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(190, 5, "Comprobante de Compra Electronico", ln=True)
        pdf.ln(10)

        # --- TABLA DE PRODUCTOS ---
        pdf.set_fill_color(198, 40, 40)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(140, 8, " Producto", fill=True)
        pdf.cell(50, 8, " Precio", fill=True, ln=True, align="C")

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 10)
        
        # Procesar los productos (Roja|5;Negra|5)
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

        # --- CLAVE GIGANTE ---
        pdf.ln(10)
        pdf.set_font("Arial", "B", 26)
        pdf.set_text_color(198, 40, 40)
        pdf.cell(190, 15, clave, ln=True, align="C")

        # --- EL PARCHE DEFINITIVO ---
        output = pdf.output(dest='S')
        # Si ya son bytes (tu caso), se mandan directo. Si es texto, se encodea.
        final_payload = output.encode('latin-1') if isinstance(output, str) else output

        return Response(
            content=final_payload,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Factura_{clave}.pdf"}
        )

    except Exception as e:
        return {"status": "error", "message": str(e)}
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
