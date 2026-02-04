import os
import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- IMPORTACIONES CORRECTAS (VERSIÓN 2025) ---

# 1. El Cerebro (LLM)
from langchain_groq import ChatGroq

# 2. PROMPTS (Esta es la línea que fallaba antes, ahora corregida)
from langchain_core.prompts import PromptTemplate

# 3. Memoria y Cadenas (Esto sigue en el paquete principal)
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory

# 4. Base de Datos y Embeddings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# 5. Reranker
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
        Inicializa el cerebro de Aura.
        """
        # Debug para saber que estamos en la versión nueva
        print("⚡ INICIANDO AURA - VERSIÓN CORREGIDA (LANGCHAIN_CORE) ⚡")

        # 1. API KEY
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            try: api_key = st.secrets["GROQ_API_KEY"]
            except: return

        # 2. LLM
        self.llm = ChatGroq(
            temperature=0.0, 
            model_name="llama-3.3-70b-versatile",
            api_key=api_key
        )
        
        # 3. EMBEDDINGS Y DB
        self.embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        if db_path.exists() and any(db_path.iterdir()):
            try:
                self.vector_db = Chroma(persist_directory=str(db_path), embedding_function=self.embedding_model)
            except Exception:
                self.vector_db = None
        else:
            self.vector_db = None
        
        # 4. RERANKER
        try:
            self.reranker_model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
            self.compressor = CrossEncoderReranker(model=self.reranker_model, top_n=5)
        except Exception:
            self.compressor = None
        
        # 5. PROMPT (Usando langchain_core)
        self.qa_prompt = PromptTemplate(
            template="""Eres Aura, Consultora Senior de 'Fashion Purse AI'.
            
            INFORMACIÓN VERIFICADA:
            {context}
            
            HISTORIAL:
            {chat_history}
            
            PREGUNTA:
            {question}
            
            Responde de forma elegante, profesional y concisa.
            """,
            input_variables=["context", "chat_history", "question"]
        )

        # 6. MEMORIA
        self.memory = ConversationBufferWindowMemory(
            k=5, 
            memory_key="chat_history",
            input_key="question",
            output_key="answer",
            return_messages=True
        )

        # 7. CADENA
        if self.vector_db and self.compressor:
            self.chain = self._build_chain()
        else:
            self.chain = None

    def _build_chain(self):
        base_retriever = self.vector_db.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 20, 'fetch_k': 50, 'lambda_mult': 0.7}
        )
        
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
        try:
            if not hasattr(self, 'chain') or self.chain is None:
                return {"answer": "⚠️ Aura no está operativa (Faltan datos).", "source_documents": []}

            return self.chain.invoke({"question": query})
            
        except Exception as e:
            if "429" in str(e):
                return {"answer": "✨ Sistemas saturados. Espera 1 min.", "source_documents": []}
            return {"answer": f"⚠️ Error: {str(e)}", "source_documents": []}