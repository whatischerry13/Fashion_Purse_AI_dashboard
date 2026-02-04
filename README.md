# 👜 Fashion Purse AI - Luxury Retail Intelligence Suite

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://fashionpurseaidashboard.streamlit.app/)
**Fashion Purse AI** es una suite de inteligencia de negocios impulsada por Inteligencia Artificial Generativa, diseñada para optimizar la toma de decisiones en el sector del retail de lujo (Bolsos y Accesorios).

Este proyecto simula el ecosistema de datos de una firma de moda ("Heras") y utiliza **Modelos de Lenguaje (LLMs)** y **Machine Learning** para ofrecer insights estratégicos, predicción de stock y asistencia virtual.

## 🚀 Características Principales

El dashboard cuenta con 9 módulos integrados:

### 🧠 Inteligencia Artificial Generativa (RAG)
- **Aura (AI Assistant):** Asistente virtual experto impulsado por **Llama 3 (vía Groq)**.
- **RAG Avanzado:** Utiliza una base de datos vectorial (**ChromaDB**) para responder preguntas sobre el catálogo, ventas y políticas internas de la empresa.
- **Memoria & Contexto:** Aura recuerda la conversación y utiliza *Rerankers* para asegurar la máxima precisión en sus respuestas.

### 📊 Módulos de Analítica & ML
1.  **Resumen General:** KPIs en tiempo real de ventas, margen y satisfacción.
2.  **Marketing Insights:** Análisis del rendimiento de campañas (ROI, CPC) y canales.
3.  **Análisis Macro:** Integración con datos demográficos y económicos (INE) para detectar oportunidades.
4.  **Simulador Estratégico:** Herramienta "What-If" para prever el impacto de cambios de precio o inversión.
5.  **Stock Inteligente:** Predicción de roturas de stock y sugerencias de reabastecimiento.
6.  **Cliente 360:** Ficha detallada de clientes con historial y CLV (Customer Lifetime Value).
7.  **Segmentación IA:** Clustering de clientes (K-Means) para identificar perfiles de comprador (VIP, Ocasional, etc.).
8.  **Cross-Selling IA:** Motor de recomendación de productos complementarios.
9.  **AI Pricing:** Modelos de elasticidad precio-demanda.

## 🛠️ Stack Tecnológico

* **Frontend:** Streamlit (Python).
* **LLM & Inference:** Groq API (Llama 3.3 70B Versatile).
* **Orquestación IA:** LangChain (Core, Community, Groq).
* **Base de Datos Vectorial:** ChromaDB.
* **Embeddings & Reranking:** HuggingFace (`sentence-transformers`, `cross-encoder`).
* **Ciencia de Datos:** Pandas, NumPy, Scikit-learn, XGBoost.
* **Visualización:** Plotly Express / Graph Objects.

## 💻 Instalación y Uso Local

Si deseas ejecutar este proyecto en tu máquina local:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/whatischerry13/Fashion_Purse_AI_dashboard](https://github.com/whatischerry13)
    cd Fashion_Purse_AI
    ```

2.  **Crear un entorno virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar variables de entorno:**
    Crea un archivo `.env` en la raíz y añade tu API Key de Groq:
    ```
    GROQ_API_KEY="gsk_tu_clave_aqui..."
    ```

5.  **Ejecutar la aplicación:**
    ```bash
    streamlit run "src/ui/Resumen General.py"
    ```

## 📂 Estructura del Proyecto

```text
Fashion_Purse_AI/
├── data/                   # Datos raw, procesados y base vectorial (Chroma)
├── src/
│   ├── rag/                # Motor de IA (engine.py, ingestión)
│   ├── ui/                 # Interfaz de usuario (Streamlit pages)
│   └── utils/              # Funciones auxiliares de carga y ML
├── requirements.txt        # Dependencias del proyecto
└── README.md               # Documentación