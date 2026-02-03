import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# --- 1. GESTIÓN DE RUTAS Y DEPENDENCIAS (Tu código original mejorado) ---
def get_project_root():
    """Encuentra la raíz del proyecto buscando la carpeta 'data' hacia arriba."""
    current = Path(__file__).resolve()
    # Subir niveles hasta encontrar data
    for _ in range(4):
        if (current / "data").exists():
            return current
        current = current.parent
    return Path(os.getcwd())

# Asegurar que la raíz está en el path del sistema para importaciones
root = get_project_root()
if str(root) not in sys.path: sys.path.append(str(root))

# Importamos el Widget de Aura (Solo si existe, para evitar errores si no has creado el archivo aún)
try:
    from src.ui.aura_sidebar import render_aura_widget
except ImportError:
    render_aura_widget = None

# --- 2. CARGA DE DATOS (Tu código original intacto) ---
@st.cache_data
def load_data():
    root = get_project_root()
    data = {}
    
    paths = {
        'forecast': root / "data/processed/forecast_horizon.csv",
        'macro': root / "data/processed/macro_indicators.csv",
        'sales': root / "data/processed/sales_history.csv",
        'metrics': root / "data/processed/daily_metrics.csv",
        'inventory': root / "data/processed/inventory_state.csv",
        'clients': root / "data/processed/clients_state.csv"
    }

    for key, path in paths.items():
        if path.exists():
            try:
                # Intentamos leer con separador automático o coma
                df = pd.read_csv(path, sep=None, engine='python')
                if 'Fecha' in df.columns: 
                    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
                data[key] = df
            except Exception as e:
                print(f"Error {key}: {e}")
                data[key] = None
        else:
            data[key] = None
            
    return data

def setup_page_config(page_title="Fashion Purse AI", layout="wide"):
    """
    Configuración centralizada + Aura Flotante.
    """
    try:
        st.set_page_config(
            page_title=page_title,
            page_icon="👜",
            layout=layout,
            initial_sidebar_state="expanded"
        )
    except:
        pass 

    # --- ESTILOS GLOBALES ---
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        section[data-testid="stSidebar"] { background-color: #F9FAFB; border-right: 1px solid #E5E7EB; }
        h1, h2, h3 { color: #111827; letter-spacing: -0.02em; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
        
        /* Ajuste para que el botón flotante no se tape con nada */
        .stChatInput { z-index: 100000; }
    </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR ESTÁNDAR (Solo Menú) ---
    with st.sidebar:
        st.markdown("### Fashion Purse AI")
        st.caption("Luxury Intelligence v2.0")
        # Aquí puedes poner logos, menú, etc. pero YA NO A AURA.
    
    # --- AURA FLOTANTE (FUERA DEL SIDEBAR) ---
    # Al ponerlo aquí, se renderiza en el root de la app y el CSS lo mueve a la esquina
    if render_aura_widget:
        render_aura_widget()
    else:
        st.toast("⚠️ Aura AI no está disponible")