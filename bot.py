import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from rag import get_rag_chain_from_disk

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

rag_chain = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if rag_chain is None:
        await update.message.reply_text(
            "¡Hola! Soy tu agente inteligente RAG.\n"
            "⚠️ Actualmente mi base de conocimientos está vacía o no ha sido generada.\n"
            "El administrador debe alimentar la base de datos localmente colocando documentos "
            "en la carpeta 'data' y ejecutando 'python ingest.py'."
        )
    else:
        await update.message.reply_text(
            "¡Hola! Soy tu agente inteligente RAG potenciado por Gemini.\n"
            "Hazme cualquier pregunta y te responderé basándome estrictamente "
            "en los documentos que han sido cargados en mi base de conocimientos local, citándolos textualmente."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    
    if rag_chain is None:
        await update.message.reply_text("Lo siento, la base de datos local no ha sido inicializada. No puedo responder preguntas aún.")
        return
        
    await update.message.reply_text("🔍 Buscando en la base de datos local y generando respuesta...")
    
    try:
        answer = rag_chain.invoke(question)
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"❌ Hubo un error al generar la respuesta: {e}")

def main():
    global rag_chain
    
    if not TELEGRAM_TOKEN or not GOOGLE_API_KEY:
        print("ERROR: Por favor configura TELEGRAM_TOKEN y GOOGLE_API_KEY en el archivo .env")
        return

    print("Cargando la base de datos vectorial local (faiss_index)...")
    rag_chain = get_rag_chain_from_disk(GOOGLE_API_KEY)
    
    if rag_chain:
        print("✅ ¡Base de datos local cargada exitosamente!")
    else:
        print("⚠️ ADVERTENCIA: No se pudo cargar la base de datos local ('faiss_index'). "
              "Asegúrate de colocar tus documentos en la carpeta 'data' y ejecutar 'python ingest.py' primero.")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot de Telegram iniciado y listo para recibir preguntas.")
    app.run_polling()

if __name__ == '__main__':
    main()
