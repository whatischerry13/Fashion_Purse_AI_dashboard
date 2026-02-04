# --- 1. PARCHE SQLITE (CRÍTICO PARA STREAMLIT CLOUD) ---
# Esto debe ir ANTES de importar ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass # Si estamos en local y no hace falta, no pasa nada
# -------------------------------------------------------

import os
import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- IMPORTACIONES LANGCHAIN ---
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# --- CONFIGURACIÓN DE RUTAS ROBUSTA ---
# Usamos os.getcwd() porque el diagnóstico nos confirmó que funciona
current_working_dir = Path(os.getcwd())
db_path = current_working_dir / 'data/chroma_db'
load_dotenv(current_working_dir / '.env')

EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class LuxuryAssistant:
    def __init__(self):
        """
        Inicializa el cerebro de Aura con diagnóstico de errores real.
        """
        # 1. API KEY
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            try: api_key = st.secrets["GROQ_API_KEY"]
            except: raise ValueError("Falta la API Key de Groq (.env o secrets)")

        # 2. LLM
        self.llm = ChatGroq(
            temperature=0.0, 
            model_name="llama-3.3-70b-versatile",
            api_key=api_key
        )
        
        # 3. EMBEDDINGS
        self.embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        # 4. CARGA DE BASE DE DATOS (PUNTO CRÍTICO)
        if not db_path.exists():
            raise FileNotFoundError(f"La carpeta DB no existe en: {db_path}")

        try:
            # Intentamos cargar Chroma
            self.vector_db = Chroma(
                persist_directory=str(db_path), 
                embedding_function=self.embedding_model
            )
            # Prueba de fuego: intentamos leer algo para ver si explota
            self.vector_db.get(limit=1) 
        except Exception as e:
            # Aquí capturamos el error real (SQLite version, permisos, etc)
            raise RuntimeError(f"Error CRÍTICO cargando ChromaDB: {str(e)}")
        
        # 5. RERANKER
        try:
            self.reranker_model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
            self.compressor = CrossEncoderReranker(model=self.reranker_model, top_n=5)
        except Exception as e:
            raise RuntimeError(f"Error cargando Reranker: {e}")
        
        # 6. PROMPT Y MEMORIA
        self.qa_prompt = PromptTemplate(
            template="""Eres Aura, experta en moda de lujo.
            CONTEXTO: {context}
            CHAT: {chat_history}
            USER: {question}
            Responde de forma breve y elegante.""",
            input_variables=["context", "chat_history", "question"]
        )

        self.memory = ConversationBufferWindowMemory(
            k=5, memory_key="chat_history", input_key="question", output_key="answer", return_messages=True
        )

        # 7. CADENA FINAL
        self.chain = self._build_chain()

    def _build_chain(self):
        base_retriever = self.vector_db.as_retriever(
            search_type="mmr", search_kwargs={'k': 20, 'fetch_k': 50, 'lambda_mult': 0.7}
        )
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor, base_retriever=base_retriever
        )
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=compression_retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt},
            return_source_documents=True
        )

    def ask(self, query):
        if not self.chain:
            return {"answer": "Error interno: Cadena no inicializada."}
        return self.chain.invoke({"question": query})