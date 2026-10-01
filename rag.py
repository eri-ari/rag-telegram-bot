import os
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=LOCAL_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

import pytesseract
from pdf2image import convert_from_path

def extract_text_from_scanned_pdf(file_path):
    try:
        images = convert_from_path(file_path)
        docs = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img)
            docs.append(Document(page_content=text, metadata={"source": file_path, "page": i+1}))
        return docs
    except Exception as e:
        print(f"Error durante OCR en el archivo {file_path}: {e}")
        return []

def load_document(file_path: str):
    ext = file_path.lower().split('.')[-1]
    
    if ext == 'pdf':
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            if not docs or all(len(d.page_content.strip()) < 10 for d in docs):
                print(f"El PDF {file_path} parece estar escaneado o sin texto reconocible, intentando OCR...")
                docs = extract_text_from_scanned_pdf(file_path)
            return docs
        except Exception as e:
            print(f"Error cargando PDF {file_path}: {e}")
            return []
            
    elif ext == 'csv':
        df = pd.read_csv(file_path)
        content = df.to_markdown()
        return [Document(page_content=content, metadata={"source": file_path})]
        
    elif ext in ['xls', 'xlsx']:
        df = pd.read_excel(file_path)
        content = df.to_markdown()
        return [Document(page_content=content, metadata={"source": file_path})]
        
    elif ext == 'md':
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return [Document(page_content=content, metadata={"source": file_path})]
        
    elif ext == 'json':
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            content = json.dumps(data, indent=2, ensure_ascii=False)
        return [Document(page_content=content, metadata={"source": file_path})]
        
    else:
        print(f"Formato no soportado: {ext}")
        return []

def build_and_save_index(data_dir: str, api_key: str, index_path: str = "faiss_index"):
    os.environ["GOOGLE_API_KEY"] = api_key
    
    docs = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_path = os.path.join(root, file)
            print(f"Procesando: {file_path}")
            docs.extend(load_document(file_path))
            
    if not docs:
        print("No se encontraron documentos válidos para indexar.")
        return False

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    total_splits = len(splits)
    print(f"Total de fragmentos (chunks) generados: {total_splits}")
    
    embeddings = get_embeddings()
    print(f"Generando embeddings locales ({LOCAL_EMBEDDING_MODEL})...")
    
    batch_size = 64
    if total_splits <= batch_size:
        vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
    else:
        print(f"Indexando en lotes de {batch_size} fragmentos...")
        vectorstore = FAISS.from_documents(documents=splits[:batch_size], embedding=embeddings)
        for i in range(batch_size, total_splits, batch_size):
            batch = splits[i:i + batch_size]
            vectorstore.add_documents(documents=batch)
            print(f"  Progreso: {min(i + batch_size, total_splits)}/{total_splits} fragmentos indexados")
            
    vectorstore.save_local(index_path)
    print(f"Base de datos vectorial guardada exitosamente en '{index_path}'")
    return True

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_rag_chain_from_disk(api_key: str, index_path: str = "faiss_index"):
    os.environ["GOOGLE_API_KEY"] = api_key
    
    if not os.path.exists(index_path):
        return None
        
    embeddings = get_embeddings()
    vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
        temperature=0.0,
        max_retries=2,
    )
    
    system_prompt = (
        "Eres un asistente virtual experto diseñado para responder preguntas basándote EXCLUSIVAMENTE "
        "en el contexto proporcionado. \n\n"
        "Reglas para contestar:\n"
        "1. Usa el contexto a continuación para responder la pregunta del usuario.\n"
        "2. Si la respuesta no está en el contexto, di explícitamente 'No puedo encontrar la respuesta en los documentos proporcionados', no inventes ni alucines información.\n"
        "3. SIEMPRE QUE SEA POSIBLE, CITA TEXTUALMENTE el documento usando comillas y mencionando el nombre del archivo o página si aplica.\n"
        "4. Tus respuestas deben ser certeras y evitar cualquier tipo de alucinación.\n\n"
        "Contexto de los documentos:\n"
        "{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    
    # Construir cadena RAG usando LangChain Expression Language (LCEL) moderno
    rag_chain = (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain
