from fastapi import FastAPI 
from databaseQR import conectar 
import pymysql
import os
from fastapi.responses import HTMLResponse 

app = FastAPI()

@app.get("/qr/ficha/{id}", response_class=HTMLResponse)
def ficha_qr(id: str):
    try:
        # 1. Intentar conectar a la base de datos
        conexion = conectar()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        
        # 2. Tu consulta SQL con el JOIN corregido
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

        # 3. Validar si existen datos
        if not data:
            return f"""
            <html>
                <body style="font-family:Arial; text-align:center; padding-top:50px;">
                    <h1>⚠️ No se encontró la ficha</h1>
                    <p>El ID {id} no existe en la base de datos.</p>
                </body>
            </html>
            """

        # 4. Retornar el HTML con los datos (Corregido estilos y variables)
        html = f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f2f2f2;
                    margin: 0;
                    padding: 20px;
                }}
                .card {{
                    background: white;
                    padding: 25px;
                    border-radius: 20px;
                    max-width: 350px;
                    margin: auto;
                    box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
                    border-top: 10px solid #ff4b2b;
                }}
                .title {{
                    text-align: center;
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    color: #333;
                }}
                .info {{
                    margin: 15px 0;
                    font-size: 16px;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 5px;
                }}
                .label {{
                    color: #ff4b2b;
                    font-weight: bold;
                    display: block;
                    font-size: 12px;
                    text-transform: uppercase;
                }}
                .emergency {{
                    margin-top: 25px;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }}
                .btn {{
                    padding: 15px;
                    border-radius: 10px;
                    text-decoration: none;
                    color: white;
                    text-align: center;
                    font-weight: bold;
                    font-size: 16px;
                }}
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
        # Esto te ayudará a ver el error real en el navegador si algo falla
        return f"<h1>Error en el servidor</h1><p>{str(e)}</p>"
