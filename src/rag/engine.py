import os
import streamlit as st
import sys

# --- IMPORTACIONES DE LANGCHAIN Y GROQ ---
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from pathlib import Path
from dotenv import load_dotenv

# --- IMPORTACIONES PARA RERANKER (Ajustadas a versiones modernas) ---
# En las versiones nuevas de LangChain (>=0.1.16), este es el camino correcto:
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
db_path = project_root / 'data/chroma_db'
load_dotenv(project_root / '.env')

# --- CONFIGURACIÓN DE MODELOS ---
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class LuxuryAssistant:
    def __init__(self):
        """
        Inicializa el cerebro de Aura (RAG + LLM).
        """
        # 1. GESTIÓN DE API KEY
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            try: 
                api_key = st.secrets["GROQ_API_KEY"]
            except: 
                print("⚠️ Error: No se encontró GROQ_API_KEY en entorno ni secrets.")
                return

        # 2. LLM (El Cerebro)
        # Nota: Al usar groq>=0.18.0 y langchain-groq actualizado, 
        # ya no hay conflicto con 'proxies'.
        self.llm = ChatGroq(
            temperature=0.0, 
            model_name="llama-3.3-70b-versatile",
            api_key=api_key
        )
        
        # 3. EMBEDDINGS Y BASE DE DATOS
        if not db_path.exists(): 
            print(f"⚠️ AVISO: La ruta de la base de datos no existe: {db_path}")
            # No lanzamos error fatal aquí para permitir que la UI cargue y muestre el aviso
        
        self.embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        # Intentamos cargar la DB solo si existe la carpeta
        if db_path.exists():
            self.vector_db = Chroma(persist_directory=str(db_path), embedding_function=self.embedding_model)
        else:
            self.vector_db = None
        
        # 4. RERANKER (El Juez de Relevancia)
        self.reranker_model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.compressor = CrossEncoderReranker(model=self.reranker_model, top_n=5)
        
        # 5. PROMPT (La Personalidad)
        self.qa_prompt = PromptTemplate(
            template="""Eres Aura, Consultora Senior de 'Fashion Purse AI'.
            
            INFORMACIÓN VERIFICADA (Top Relevancia):
            {context}
            
            HISTORIAL:
            {chat_history}
            
            PREGUNTA:
            {question}
            
            REGLAS:
            1. **NO REGATEO:** Precios fijos. Calidad garantizada.
            2. **VENTA:** Si el contexto tiene productos, véndelos con elegancia.
            3. **GEOGRAFÍA:** España = 24h.
            4. **PRECISIÓN:** Usa solo los datos proporcionados.
            
            RESPUESTA:""",
            input_variables=["context", "chat_history", "question"]
        )

        # 6. MEMORIA (Corto Plazo)
        self.memory = ConversationBufferWindowMemory(
            k=5, 
            memory_key="chat_history",
            input_key="question",
            output_key="answer",
            return_messages=True
        )

        # 7. CONSTRUCCIÓN DE LA CADENA
        if self.vector_db:
            self.chain = self._build_chain()
        else:
            print("⚠️ AVISO: No se pudo construir la cadena (Falta VectorDB)")

    def _build_chain(self):
        """Construye la cadena lógica (Buscador -> Reranker -> LLM)"""
        # A. Buscador amplio
        base_retriever = self.vector_db.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 20, 'fetch_k': 50, 'lambda_mult': 0.7}
        )
        
        # B. Filtro de calidad (Reranker)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor,
            base_retriever=base_retriever
        )
        
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=compression_retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt},
            return_source_documents=True
        )

    def ask(self, query):
        """
        Método PÚBLICO y SEGURO.
        """
        try:
            # Verificación de seguridad antes de invocar
            if not hasattr(self, 'chain'):
                return {
                    "answer": "⚠️ *Error de Inicialización:* No puedo acceder a mi base de datos de conocimiento. Verifica que los archivos 'chroma_db' estén subidos al repositorio.", 
                    "source_documents": []
                }

            # Ejecutar la cadena
            return self.chain.invoke({"question": query})
            
        except Exception as e:
            error_msg = str(e)
            # Manejo específico de Rate Limit (Error 429)
            if "429" in error_msg or "Rate limit" in error_msg:
                return {
                    "answer": "✨ *Mis sistemas están saturados momentáneamente. Por favor, espera un minuto.* 🧘‍♀️",
                    "source_documents": []
                }
            else:
                return {
                    "answer": f"⚠️ *Error técnico:* {str(e)[:100]}...",
                    "source_documents": []
                }