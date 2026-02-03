import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import sys
import os
import shutil
from pathlib import Path

# --- CONFIGURACIÓN ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
data_path = project_root / 'data'
db_path = project_root / 'data/chroma_db'

# Usamos un modelo que ENTIENDE ESPAÑOL y relaciones complejas
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def ingest_catalog_complete():
    print("🚀 [AI BRAIN] Iniciando INGESTA MULTILINGÜE DE ALTA PRECISIÓN...")
    
    # 1. Borrado de seguridad (Reset total)
    if db_path.exists():
        print("   🧹 Limpiando base de datos antigua...")
        shutil.rmtree(db_path)
    
    documents = []
    
    # 2. PROCESAR MANUAL OPERATIVO (Con peso semántico alto)
    path_faqs = data_path / 'processed/corporate_knowledge.txt'
    if path_faqs.exists():
        with open(path_faqs, 'r', encoding='utf-8') as f:
            full_text = f.read()
            blocks = full_text.split('## ')
            for block in blocks:
                if block.strip():
                    # Añadimos contexto explícito para que no se pierda
                    content = f"CONTEXTO EMPRESARIAL: {block.strip()}"
                    documents.append(Document(page_content=content, metadata={"source": "faq", "type": "rule"}))
    
    # 3. PROCESAR BOLSOS CON "TRADUCCIÓN DE PRECIOS"
    path_bags = data_path / 'raw/luxury_handbags.csv'
    if path_bags.exists():
        df_bags = pd.read_csv(path_bags)
        print(f"   👜 Optimizando {len(df_bags)} productos de lujo...")
        
        for _, row in df_bags.iterrows():
            price = float(row['Precio_Venta_EUR'])
            
            # ESTRATEGIA: Convertir números a conceptos semánticos
            # Esto permite buscar "bolsos caros" o "inversión" y encontrar los de precio alto
            if price > 5000:
                price_concept = "Rango Precio: Muy Alto. Categoría: Inversión Exclusiva Ultra Lujo."
            elif price > 1500:
                price_concept = "Rango Precio: Alto. Categoría: Lujo Premium."
            elif price > 800:
                price_concept = "Rango Precio: Medio-Alto. Categoría: Lujo Estándar."
            else:
                price_concept = "Rango Precio: Accesible. Categoría: Entrada al Lujo."

            content = (
                f"ARTÍCULO: Bolso de Lujo. MARCA: {row['Marca']}. MODELO: {row['Modelo']}. "
                f"PRECIO: {price} EUR. ({price_concept}) "
                f"MATERIAL: {row['Material']}. COLOR: {row['Color']}. "
                f"ESTADO: {row['Estado_General']}. "
                f"DESCRIPCIÓN: Pieza auténtica verificada."
            )
            
            meta = {
                "source": "catalog",
                "brand": row['Marca'],
                "price": price
            }
            documents.append(Document(page_content=content, metadata=meta))

    # 4. VECTORIZACIÓN MULTILINGÜE
    if documents:
        print(f"   🧠 Creando conexiones neuronales en Español ({EMBEDDING_MODEL_NAME})...")
        # Este modelo descargará unos 400MB la primera vez, es normal.
        embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        vector_db = Chroma.from_documents(
            documents=documents,
            embedding=embedding_model,
            persist_directory=str(db_path)
        )
        print("✅ CEREBRO ACTUALIZADO Y OPTIMIZADO EN ESPAÑOL.")
    else:
        print("❌ Error: No se encontraron documentos.")

if __name__ == "__main__":
    ingest_catalog_complete()