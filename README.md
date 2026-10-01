# Telegram RAG Bot con Gemini 1.5 Pro

Este bot de Telegram te permite subir archivos PDF (normales y escaneados), CSV y Excel (.xls, .xlsx) y realizar preguntas sobre ellos utilizando **Gemini 1.5 Pro**. El bot está instruido para responder citando textualmente el contenido de los documentos y sin alucinar respuestas.

## Requisitos Previos
1. **Python 3.9+** instalado.
2. **Tokens y API Keys**:
   - `TELEGRAM_TOKEN`: Obtenido hablando con [BotFather](https://t.me/botfather) en Telegram.
   - `GOOGLE_API_KEY`: Obtenido desde Google AI Studio (Gemini).

## Configuración de OCR para Windows (Para PDFs Escaneados)
Si planeas subir PDFs que son imágenes escaneadas, necesitas instalar Tesseract y Poppler en tu sistema:
1. **Tesseract OCR**: 
   - Descarga el instalador desde [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) e instálalo.
   - Añade la ruta de instalación (ej. `C:\Program Files\Tesseract-OCR`) a las variables de entorno `PATH` de tu sistema.
2. **Poppler** (necesario para convertir PDF a imagen):
   - Descarga la última "Release" desde [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/).
   - Extrae el `.zip` en una carpeta (ej. `C:\poppler`) y añade la ruta de su subcarpeta `bin` (ej. `C:\poppler\bin`) a las variables de entorno `PATH`.

## Instalación
1. Renombra el archivo `.env.example` a `.env` e ingresa tus claves.
2. Abre una terminal y navega hasta esta carpeta.
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución
Ejecuta el bot usando el siguiente comando:
```bash
python bot.py
```

## Uso en Telegram
1. Busca tu bot en Telegram.
2. Usa el comando `/start`.
3. Envía un archivo (PDF, CSV o Excel). El bot te confirmará que lo ha procesado.
4. Escribe cualquier pregunta relacionada a tu archivo. El bot te contestará basándose estrictamente en el contenido.
5. Puedes enviar `/clear` para borrar el contexto y empezar con otros documentos.
