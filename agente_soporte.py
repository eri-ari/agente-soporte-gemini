import json
import os
import time
import schedule
import gspread
from google import genai
from google.genai import types

# --- Configuración ---
ARCHIVO_CREDENCIALES = 'client_secrets.json'
NOMBRE_HOJA = 'Comentarios'
GEMINI_API_KEY = 'TU_API_KEY_AQUI' # REEMPLAZA CON TU API KEY
INTERVALO_MINUTOS = 2

# Índices de columnas (1-indexed en gspread)
COLUMNA_CLASIFICACION = 4 # D
COLUMNA_SENTIMIENTO = 5   # E
COLUMNA_EJECUTADO = 6     # F

# Cliente global de Gemini
gemini_client = None

def conectar_sheets():
    """Conecta con Google Sheets usando OAuth 2.0 y retorna la hoja."""
    try:
        # Autenticar usando el archivo JSON descargado
        gc = gspread.oauth(credentials_filename=ARCHIVO_CREDENCIALES)
        # Abrir la hoja por su nombre
        sh = gc.open(NOMBRE_HOJA)
        # Retornar la primera hoja (sheet1)
        return sh.sheet1
    except Exception as e:
        import traceback
        print(f"Error al conectar con Google Sheets: {e}")
        print(traceback.format_exc())
        return None

def analizar_con_gemini(comentario):
    """Envía el comentario a Gemini para analizar clasificación y sentimiento."""
    try:
        instruccion_sistema = (
            "Eres un analista de soporte al cliente. Tu única tarea es devolver una "
            "respuesta en formato JSON estricto, sin texto adicional ni explicaciones."
        )
        
        instruccion_usuario = (
            f"Analiza el siguiente comentario de un cliente:\n'{comentario}'\n"
            "1. Clasifícalo en una de estas tres categorías: 'Ventas', 'Soporte Técnico' o 'Logística'.\n"
            "2. Detecta el sentimiento: 'Positivo', 'Negativo' o 'Neutro'.\n"
            "Devuelve el resultado como un JSON con las claves 'clasificacion' y 'sentimiento'."
        )

        response = gemini_client.models.generate_content(
            model='gemini-3.5-flash',
            contents=instruccion_usuario,
            config=types.GenerateContentConfig(
                system_instruction=instruccion_sistema,
                temperature=0.0
            )
        )
        
        texto_respuesta = response.text
        
        # Limpiar posibles bloques de código Markdown
        if texto_respuesta.startswith('```'):
            texto_respuesta = texto_respuesta.strip('`')
            if texto_respuesta.lower().startswith('json'):
                texto_respuesta = texto_respuesta[4:]
            texto_respuesta = texto_respuesta.strip()
            
        return json.loads(texto_respuesta)
        
    except Exception as e:
        print(f"Error al analizar con Gemini: {e}")
        return None

def ejecutar_agente():
    """Orquesta el ciclo completo del agente."""
    print("\nIniciando ejecución del agente...")
    hoja = conectar_sheets()
    if not hoja:
        print("No se pudo obtener la hoja. Abortando ciclo.")
        return

    try:
        # Obtener todas las filas
        filas = hoja.get_all_values()
        
        # Omitir la primera fila (encabezados) y procesar el resto
        for i, fila in enumerate(filas):
            if i == 0:
                continue # Saltar encabezados
                
            numero_fila = i + 1 # gspread usa índices base 1
            
            # Asegurarse de que la fila tenga suficientes columnas para revisar F
            ya_ejecutado = ""
            if len(fila) >= 6:
                ya_ejecutado = fila[5]
                
            if ya_ejecutado.strip().upper() == "SI":
                continue # Fila ya procesada
                
            # Extraer comentario (Columna C)
            comentario = ""
            if len(fila) >= 3:
                comentario = fila[2]
                
            cliente = "Desconocido"
            if len(fila) >= 2 and fila[1].strip() != "":
                cliente = fila[1]
                
            if not comentario.strip():
                continue # Comentario vacío
                
            print(f"Procesando comentario de: {cliente}...")
            
            # Analizar con Gemini
            resultado = analizar_con_gemini(comentario)
            
            if resultado and isinstance(resultado, dict):
                clasificacion = resultado.get("clasificacion", "")
                sentimiento = resultado.get("sentimiento", "")
                
                print(f"  -> Clasificación: {clasificacion} | Sentimiento: {sentimiento}")
                
                # Escribir en la hoja
                try:
                    hoja.update_cell(numero_fila, COLUMNA_CLASIFICACION, clasificacion)
                    hoja.update_cell(numero_fila, COLUMNA_SENTIMIENTO, sentimiento)
                    hoja.update_cell(numero_fila, COLUMNA_EJECUTADO, "SI")
                except Exception as e:
                    print(f"Error al escribir en Google Sheets (Fila {numero_fila}): {e}")
            else:
                print(f"  -> No se obtuvo un JSON válido de Gemini para la fila {numero_fila}.")
                
    except Exception as e:
        print(f"Error durante el ciclo de ejecución: {e}")

if __name__ == "__main__":
    # Validar API Key
    if GEMINI_API_KEY == 'TU_API_KEY_AQUI':
        print("ERROR: Debes reemplazar 'TU_API_KEY_AQUI' con tu API Key real de Gemini.")
        exit(1)
        
    # Validar credenciales
    if not os.path.exists(ARCHIVO_CREDENCIALES):
        print(f"ERROR: No se encontró el archivo de credenciales '{ARCHIVO_CREDENCIALES}'.")
        print("Por favor, colócalo en la misma carpeta que este script.")
        exit(1)
        
    # Inicializar cliente de Gemini
    print("Inicializando cliente de Gemini...")
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Ejecutar inmediatamente
    ejecutar_agente()
    
    # Programar ejecuciones automáticas
    print(f"Programando el agente para que se ejecute cada {INTERVALO_MINUTOS} minutos...")
    schedule.every(INTERVALO_MINUTOS).minutes.do(ejecutar_agente)
    
    # Mantener el script corriendo
    while True:
        schedule.run_pending()
        time.sleep(30)
