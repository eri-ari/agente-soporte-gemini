# Agente de Soporte con Gemini y Google Sheets

Este agente se conecta a una hoja de cálculo de Google Sheets, lee comentarios de clientes en tiempo real y utiliza la IA de Gemini para analizar la **clasificación** (Ventas, Soporte Técnico, Logística) y el **sentimiento** (Positivo, Negativo, Neutro) de cada comentario.

## Requisitos

1. Python 3.x
2. Archivo `client_secrets.json` de un cliente OAuth 2.0 (Google Cloud Console).
3. Una API Key de Google Gemini.

## Instalación

1. Clona el repositorio.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Edita el archivo `agente_soporte.py` y coloca tu API Key de Gemini donde dice `TU_API_KEY_AQUI`.
4. Coloca tu archivo `client_secrets.json` en la raíz de este proyecto.

## Uso

Ejecuta el agente desde la terminal:
```bash
python agente_soporte.py
```

La primera vez que lo ejecutes, abrirá una ventana en tu navegador para que inicies sesión con tu cuenta de Google y autorices el acceso a tus hojas de cálculo. Luego se ejecutará en bucle procesando las filas nuevas según el intervalo configurado.
