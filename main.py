from fastapi import FastAPI #esto sirve para importar la libreria de FastAPI es mi framework
from databaseQR import conectar #de otro archivo .py traigo una funcion
import pymysql
from fastapi.responses import HTMLResponse #devolvere  html no json


app = FastAPI()
@app.get("/qr/ficha/{id}" , response_class=HTMLResponse)
def ficha_qr(id : str):
    conexion = conectar()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    sql = """
    SELECT 
        p.Nombre,
        p.Apellido,
        f.Tipo_Sangre,
        f.Alergias,
        f.Observaciones
     FROM FICHAS_MEDICAS f
    JOIN PERSONAS p 
    ON f.ID_Persona = p.ID_Personas
    WHERE f.ID_Ficha = %s
"""

    cursor.execute(sql, (id,))
    
    data = cursor.fetchone()
    conexion.close()
    if not data:
        return "<h1>No se encontro la ficha</h1>"
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family:Arial;
                bacground: #f2f2f2;
                margin: 0;
                padding:20px;
            }}
            .card{{
                backgrouund: white;
                padding:20px;
                border-radius:20px;
                max-width:350px;
                margin : auto;
                box-shadow: 0px 4px 15px rgba(0,0,0,0.2)
            }}
            .title {{
                text-align: center;
                font-size: 22px;
                font-weight: bold;
            }}

            .info {{
                margin: 10px 0;
            }}

            .emergency {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}

            .btn {{
                padding: 12px;
                border-radius: 10px;
                text-decoration: none;
                color: white;
                text-align: center;
                font-weight: bold;
            }}

            .btn911 {{
                background: red;
            }}

            .btn132 {{
                background: blue;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class= "title">Ficha Medica</div>
            
          <div class="info"><b>Nombre:</b> {data['Nombre']} {data['Apellido']}</div>
            <div class="info"><b>Tipo de sangre:</b> {data['Tipo_Sangre']}</div>
            <div class="info"><b>Alergias:</b> {data['Alergias']}</div>
            <div class="info"><b>Observaciones:</b> {data['Observaciones']}</div>
        </div>

        <div class="emergency">
            <a class="btn btn911" href="tel:911">📞 EMERGENCIAS</a>
            <a class="btn btn132" href="tel:132">📞 SEM</a>
        </div>

    </body>
    </html>
    """

    return html

    
    