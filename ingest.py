import os
from dotenv import load_dotenv
from rag import build_and_save_index

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DATA_DIR = "data"

if __name__ == "__main__":
    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY no encontrada en el archivo .env")
        exit(1)
        
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Se ha creado la carpeta '{DATA_DIR}'. Por favor, coloca tus archivos PDF, CSV, Excel, MD o JSON ahí y vuelve a ejecutar este script.")
        exit(0)
        
    print(f"Iniciando ingesta de documentos desde la carpeta local '{DATA_DIR}'...")
    success = build_and_save_index(DATA_DIR, GOOGLE_API_KEY)
    
    if success:
        print("Ingesta completada. Ahora puedes iniciar el bot ejecutando 'python bot.py'.")
    else:
        print("La ingesta falló o no hubo documentos para procesar en la carpeta de datos.")
