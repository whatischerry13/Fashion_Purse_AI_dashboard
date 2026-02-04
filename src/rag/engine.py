import os
import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv

# --- IMPORTACIONES ESTABLES (LangChain 0.1.20) ---
from langchain_groq import ChatGroq
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory

# Rerankers
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
        Inicializa el cerebro de Aura (Versión Estable).
        """
        # 1. API KEY
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            try: api_key = st.secrets["GROQ_API_KEY"]
            except: return

        # 2. LLM (Cerebro)
        self.llm = ChatGroq(
            temperature=0.0, 
            model_name="llama-3.3-70b-versatile",
            api_key=api_key
        )
        
        # 3. EMBEDDINGS Y BASE DE DATOS
        self.embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        if db_path.exists() and any(db_path.iterdir()):
            try:
                self.vector_db = Chroma(persist_directory=str(db_path), embedding_function=self.embedding_model)
            except Exception as e:
                print(f"Error DB: {e}")
                self.vector_db = None
        else:
            self.vector_db = None
        
        # 4. RERANKER
        try:
            self.reranker_model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
            self.compressor = CrossEncoderReranker(model=self.reranker_model, top_n=5)
        except:
            self.compressor = None
        
        # 5. PROMPT
        self.qa_prompt = PromptTemplate(
            template="""Eres Aura, Consultora Senior de 'Fashion Purse AI'.
            
            INFORMACIÓN VERIFICADA:
            {context}
            
            HISTORIAL:
            {chat_history}
            
            PREGUNTA:
            {question}
            
            Responde de forma profesional, breve y elegante.
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
        # A. Buscador
        base_retriever = self.vector_db.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 20, 'fetch_k': 50, 'lambda_mult': 0.7}
        )
        
        # B. Reranker
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=self.compressor,
            base_retriever=base_retriever
        )
        
        # C. Cadena Conversacional (Aquí es donde daba el error, ahora funcionará)
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
                return {"answer": "⚠️ Aura no operativa (Falta DB).", "source_documents": []}

            return self.chain.invoke({"question": query})
            
        except Exception as e:
            if "429" in str(e):
                return {"answer": "✨ Sistemas saturados. Espera 1 min.", "source_documents": []}
            return {"answer": f"⚠️ Error: {str(e)}", "source_documents": []}