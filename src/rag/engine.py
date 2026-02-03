import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from pathlib import Path
from dotenv import load_dotenv

# --- NUEVAS IMPORTACIONES PARA EL RERANKER ---
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
db_path = project_root / 'data/chroma_db'
load_dotenv(project_root / '.env')

EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class LuxuryAssistant:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            try: api_key = st.secrets["GROQ_API_KEY"]
            except: return

        # 1. LLM (Cerebro)
        self.llm = ChatGroq(
            temperature=0.0, 
            model_name="llama-3.3-70b-versatile",
            api_key=api_key
        )
        
        # 2. Embeddings
        if not db_path.exists(): raise FileNotFoundError("DB Missing")
        self.embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        self.vector_db = Chroma(persist_directory=str(db_path), embedding_function=self.embedding_model)
        
        # 3. RERANKER (El Juez)
        self.reranker_model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.compressor = CrossEncoderReranker(model=self.reranker_model, top_n=5)
        
        # 4. PROMPT
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

        # 5. MEMORIA
        self.memory = ConversationBufferWindowMemory(
            k=5, 
            memory_key="chat_history",
            input_key="question",
            output_key="answer",
            return_messages=True
        )

        # 6. IMPORTANTE: CREAMOS LA CADENA AQUÍ
        self.chain = self._build_chain()

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
        Maneja errores (como el 429) sin romper la app.
        """
        try:
            if not hasattr(self, 'chain'):
                return {"answer": "⚠️ Error: Aura no se inicializó correctamente.", "source_documents": []}

            # Ejecutar la cadena
            return self.chain.invoke({"question": query})
            
        except Exception as e:
            error_msg = str(e)
            # Manejo de error 429 (Rate Limit)
            if "429" in error_msg or "Rate limit" in error_msg:
                return {
                    "answer": "✨ *Mis sistemas neuronales están saturados por el alto volumen de consultas VIP. Por favor, espera un minuto mientras libero recursos de procesamiento.* 🧘‍♀️",
                    "source_documents": []
                }
            else:
                return {
                    "answer": f"⚠️ *Lo siento, he tenido un pequeño fallo técnico. ¿Podrías repetirme la pregunta?* (Code: {str(e)[:20]}...)",
                    "source_documents": []
                }