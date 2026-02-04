import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import datetime
import os
# --- IMPORTAR AURA ---
try:
    from src.ui.aura_component import render_aura
except ImportError:
    pass
# 1. Importar common (que ya incluye el path root)
from src.ui.common import setup_page_config, get_project_root, load_data

# 2. Configurar página + Cargar Aura (Todo en una línea)
setup_page_config(page_title="Pricing Lab", layout="wide")

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.ui.common import load_data

st.set_page_config(page_title="AI Sales Terminal", layout="wide")

# --- CSS PREMIUM (Strict Corporate - Clean) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* TARJETA DE PRODUCTO */
    .rec-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 25px;
        margin-bottom: 20px;
        border-left: 4px solid #0F172A;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: border-color 0.3s;
    }
    .rec-card:hover {
        border-left-color: #2563EB;
    }
    
    .badge-reason {
        background-color: #F1F5F9; color: #475569;
        font-size: 11px; font-weight: 700; text-transform: uppercase;
        padding: 4px 8px; border-radius: 2px; letter-spacing: 0.05em;
        cursor: default; /* Indica que hay tooltip */
        border-bottom: 1px dotted #94A3B8;
    }
    
    .price-tag { font-size: 18px; font-weight: 700; color: #0F172A; }
    .margin-tag { font-size: 12px; color: #15803D; font-weight: 600; }
    
    /* HEADER CLIENTE */
    .client-header {
        background: #FFFFFF; padding: 25px; border-radius: 6px; border: 1px solid #E2E8F0;
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;
    }
    
    /* BUNDLE CARD */
    .bundle-box {
        background-color: #FFFFFF; border: 1px solid #CBD5E1; 
        padding: 20px; border-radius: 8px; margin-top: 10px;
    }
    
    h1, h2, h3, h4 { color: #0F172A; font-family: 'Inter', sans-serif; font-weight: 700; letter-spacing: -0.02em; }
    .stButton>button { width: 100%; border-radius: 4px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- UTILS & DATA LOADING ---

def format_euro(val):
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def clean_segment_string(segment_name):
    """Elimina emojis y deja texto limpio corporativo."""
    if not isinstance(segment_name, str): return "Standard"
    clean = segment_name.encode('ascii', 'ignore').decode('ascii').strip()
    clean = clean.replace('Durmientes / Inactivos', 'Inactivos')
    clean = clean.replace('Top VIC (Elite)', 'Elite VIC')
    clean = clean.replace('Retornadores Seriales', 'Riesgo')
    clean = clean.replace('Brand Lovers (Fieles)', 'Fidelizados')
    clean = clean.replace('Smart Shoppers (Accesorios)', 'Smart Shoppers')
    clean = clean.replace('Standard / Nuevos', 'Standard')
    return clean.strip()

def get_reason_explanation(reason_text):
    """Genera el texto del tooltip para explicar el porqué. Incluye manejo de errores."""
    
    # --- FIX CRÍTICO: Validación de tipo de dato ---
    if not isinstance(reason_text, str):
        return "Recomendación basada en afinidad de perfil e historial."
    
    reason_lower = reason_text.lower()
    
    if "mantenimiento" in reason_lower:
        return "Sugerencia basada en ciclo de vida: La última compra fue hace más de 1 año."
    if "match" in reason_lower or "colección" in reason_lower:
        return "Sugerencia basada en estética: El producto coincide con la marca o estilo de la última compra."
    if "cuidado" in reason_lower:
        return "Venta cruzada directa: Producto complementario de bajo coste para proteger la compra principal."
    if "vip" in reason_lower or "joyería" in reason_lower:
        return "Afinidad de perfil: Este segmento (VIC) tiene alta propensión a comprar joyería de alto valor."
        
    return "Recomendación basada en el historial de transacciones y perfil del cliente."

@st.cache_data
def load_data_engine():
    try:
        # Cargar Recomendaciones
        rec_path = project_root / 'data/processed/recommendations_matrix.csv'
        if not rec_path.exists(): return None, None, None
        
        # Leer CSV manejando NaNs como strings vacíos para evitar errores futuros
        df_recs = pd.read_csv(rec_path).fillna({'Reason': 'Recomendación General'})
        
        # Cargar Clientes
        clients_path = project_root / 'data/raw/clients.csv'
        df_clients = pd.read_csv(clients_path)
        
        # Cargar Clusters y limpiar nombres
        cluster_path = project_root / 'data/processed/clients_clusters.csv'
        if cluster_path.exists():
            df_clusters = pd.read_csv(cluster_path)
            # Detectar columna correcta
            seg_col = 'Segmento_Clean' if 'Segmento_Clean' in df_clusters.columns else 'Segmento_IA'
            
            # Limpiar emojis ANTES del merge
            df_clusters['Segmento_Limpio'] = df_clusters[seg_col].apply(clean_segment_string)
            
            df_clients = pd.merge(df_clients, df_clusters[['Client_ID', 'Segmento_Limpio']], on='Client_ID', how='left')
            df_clients.rename(columns={'Segmento_Limpio': 'Segmento'}, inplace=True)
            df_clients['Segmento'] = df_clients['Segmento'].fillna('Standard')
        else:
            df_clients['Segmento'] = 'Standard'
            
        return df_recs, df_clients
    except Exception as e:
        st.error(f"Error técnico cargando datos: {e}")
        return None, None

# --- SISTEMA DE MEMORIA (FEEDBACK LOOP) ---
def save_rejection(client_id, product_name):
    """Guarda en un CSV persistente que este cliente rechazó este producto."""
    feedback_path = project_root / 'data/processed/feedback_log.csv'
    
    # Crear archivo si no existe
    if not feedback_path.exists():
        pd.DataFrame(columns=['Client_ID', 'Product_Name', 'Action', 'Date']).to_csv(feedback_path, index=False)
    
    new_entry = pd.DataFrame([{
        'Client_ID': client_id,
        'Product_Name': product_name,
        'Action': 'Rejected',
        'Date': datetime.datetime.now().strftime("%Y-%m-%d")
    }])
    
    new_entry.to_csv(feedback_path, mode='a', header=False, index=False)

def get_rejected_products(client_id):
    """Lee el CSV y devuelve lista de productos rechazados por este cliente."""
    feedback_path = project_root / 'data/processed/feedback_log.csv'
    if not feedback_path.exists(): return []
    
    try:
        df_feed = pd.read_csv(feedback_path)
        rejected = df_feed[(df_feed['Client_ID'] == client_id) & (df_feed['Action'] == 'Rejected')]
        return rejected['Product_Name'].tolist()
    except:
        return []

# --- GENERADOR DE TEXTO ---
def generate_copy(client_name, product_name, context_item, reason, channel, segment):
    # Validación segura de strings
    if not isinstance(reason, str): reason = "afinidad"
    if not isinstance(context_item, str): context_item = "su colección"
    
    first_name = client_name.split()[0]
    is_formal = segment in ['Elite VIC', 'Inactivos', 'Investor', 'Classic']
    
    if channel == "WhatsApp":
        if is_formal:
            return f"Hola {first_name}, le escribo de Heras Purse. Espero que disfrute su {context_item}. Hemos recibido una pieza exclusiva que encaja con su perfil: {product_name}. ¿Le envío detalles?"
        else:
            return f"Hola {first_name}! He visto este {product_name} y me he acordado de ti por tu {context_item}. Hacen un juego perfecto. Te paso fotos?"
    else: # Email
        subject = f"Novedad exclusiva para su colección {context_item}"
        body = f"Estimado/a {first_name},\n\nSeleccionamos para usted el {product_name} basándonos en su historial.\nMotivo: {reason}.\n\nSaludos,\nEquipo Heras."
        return f"ASUNTO: {subject}\n\n{body}"

# --- APP PRINCIPAL ---

df_recs, df_clients = load_data_engine()

if df_recs is None:
    st.error("Error de conexión con el motor de datos.")
    st.stop()

# ==============================================================================
# SIDEBAR: FILTROS AVANZADOS
# ==============================================================================
with st.sidebar:
    st.markdown("### Filtros de Cartera")
    
    # 1. Filtro de Ubicación
    all_cities = sorted(df_clients['City'].dropna().unique())
    selected_cities = st.multiselect("Ubicación / Zona", all_cities, placeholder="Todas las ciudades")
    
    # 2. Filtro de Segmento (Limpio)
    all_segments = sorted(df_clients['Segmento'].unique())
    selected_segments = st.multiselect("Perfil Estratégico", all_segments, placeholder="Todos los perfiles")
    
    # Aplicar Filtros
    filtered_clients = df_clients.copy()
    if selected_cities:
        filtered_clients = filtered_clients[filtered_clients['City'].isin(selected_cities)]
    if selected_segments:
        filtered_clients = filtered_clients[filtered_clients['Segmento'].isin(selected_segments)]
    
    # Filtro adicional: Solo clientes con recomendaciones
    active_ids = df_recs['Client_ID'].unique()
    filtered_clients = filtered_clients[filtered_clients['Client_ID'].isin(active_ids)]
    
    st.divider()
    
    # 3. Selector Final
    st.markdown(f"**Clientes Encontrados:** {len(filtered_clients)}")
    
    client_options = filtered_clients.apply(lambda x: f"{x['Name']} ({x['Client_ID']})", axis=1).tolist()
    selected_search = st.selectbox("Seleccionar Cliente", client_options, index=None, placeholder="Buscar nombre o ID...")
    
    current_client_id = None
    if selected_search:
        current_client_id = selected_search.split('(')[1].replace(')', '')
        client_info = df_clients[df_clients['Client_ID'] == current_client_id].iloc[0]
        
        # INFO EXTRA (EMAIL RESTAURADO)
        st.info(f"Email: {client_info['Email']}")
        st.caption(f"{client_info['City']} | {client_info['Segmento']}")

# ==============================================================================
# ÁREA PRINCIPAL
# ==============================================================================

st.title("AI Sales Terminal")
st.markdown("Plataforma de inteligencia comercial y activación de cross-selling.")

if current_client_id:
    # Cargar recomendaciones y filtrar las rechazadas (MEMORIA)
    raw_recs = df_recs[df_recs['Client_ID'] == current_client_id].copy()
    rejected_list = get_rejected_products(current_client_id)
    active_recs = raw_recs[~raw_recs['Product_Name'].isin(rejected_list)]
    
    # Header Cliente
    st.markdown(f"""
    <div class="client-header">
        <div>
            <div style="font-size:24px; font-weight:700; color:#0F172A;">{client_info['Name']}</div>
            <div style="color:#64748B; margin-top:5px;">
                Segmento: <b style="color:#0F172A;">{client_info['Segmento']}</b>
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:12px; color:#64748B; text-transform:uppercase; letter-spacing:0.05em;">Oportunidades</div>
            <div style="font-size:28px; font-weight:700; color:#16A34A;">{len(active_recs)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # EXPLICABILIDAD (TRANSPARENCIA)
    with st.expander("Información del Modelo (Lógica de Decisión)", expanded=False):
        context_show = active_recs.iloc[0]['Context_Item'] if not active_recs.empty else 'General'
        if not isinstance(context_show, str): context_show = "General"
        
        st.markdown(f"""
        El modelo ha analizado el perfil de **{client_info['Name']}** cruzando 3 factores clave:
        1.  **Afinidad de Marca:** Se detectan patrones con la marca **{context_show}**.
        2.  **Ciclo de Vida:** Se calcula el tiempo desde la última transacción para sugerir mantenimiento o novedades.
        3.  **Perfil Estratégico:** Ajuste de productos según la capacidad de gasto y comportamiento del segmento **{client_info['Segmento']}**.
        """)

    if active_recs.empty:
        if not raw_recs.empty:
            st.warning("Todas las recomendaciones disponibles han sido descartadas manualmente.")
        else:
            st.info("No hay oportunidades claras de cross-selling bajo los criterios actuales.")
    
    else:
        # Layout Columnas
        col_recs, col_bundle = st.columns([2, 1])
        
        with col_recs:
            st.markdown("### Recomendaciones Prioritarias")
            
            for i, row in active_recs.iterrows():
                product_name = row['Product_Name']
                reason_val = row['Reason'] if isinstance(row['Reason'], str) else "Recomendación IA"
                tooltip_text = get_reason_explanation(reason_val)
                
                # Tarjeta de Producto con Tooltip en Badge
                st.markdown(f"""
                <div class="rec-card">
                    <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                        <span class="badge-reason" title="{tooltip_text}">{reason_val}</span>
                        <span class="margin-tag">Margen: +{format_euro(row['Margin'])}</span>
                    </div>
                    <div style="font-size:18px; font-weight:700; margin-bottom:5px; color:#1E293B;">{product_name}</div>
                    <div style="font-size:14px; color:#64748B; margin-bottom:15px;">
                        Precio: <b>{format_euro(row['Price'])}</b> | Contexto: {row['Context_Item']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Acciones
                c_msg, c_feed = st.columns([3, 1])
                
                with c_msg:
                    tab_wa, tab_em = st.tabs(["WhatsApp", "Email"])
                    with tab_wa:
                        st.text_area("Mensaje:", value=generate_copy(client_info['Name'], product_name, row['Context_Item'], reason_val, "WhatsApp", client_info['Segmento']), height=80, key=f"w{i}")
                    with tab_em:
                        st.text_area("Borrador:", value=generate_copy(client_info['Name'], product_name, row['Context_Item'], reason_val, "Email", client_info['Segmento']), height=150, key=f"e{i}")

                with c_feed:
                    st.write("") # Spacer
                    st.write("")
                    if st.button("Registrar Venta", key=f"sold_{i}", help="Marcar como vendido y actualizar métricas"):
                        st.success("Venta registrada correctamente.")
                        # Lógica futura: Actualizar DB ventas
                    
                    if st.button("Descartar", key=f"rej_{i}", help="Eliminar esta sugerencia para el futuro"):
                        save_rejection(current_client_id, product_name)
                        st.rerun()

        # THE TOTAL LOOK (BUNDLE)
        with col_bundle:
            if len(active_recs) >= 2:
                st.markdown("### The Total Look")
                item1 = active_recs.iloc[0]
                item2 = active_recs.iloc[1]
                total = item1['Price'] + item2['Price']
                deal = total * 0.95
                
                st.markdown(f"""
                <div class="bundle-box">
                    <h4 style="margin-top:0;">Pack Sugerido</h4>
                    <ul style="color:#475569; font-size:14px; padding-left:20px;">
                        <li>{item1['Product_Name']}</li>
                        <li>{item2['Product_Name']}</li>
                    </ul>
                    <hr style="border-top: 1px solid #E2E8F0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="text-decoration:line-through; color:#94A3B8;">{format_euro(total)}</span>
                        <span style="font-size:20px; font-weight:700; color:#0F172A;">{format_euro(deal)}</span>
                    </div>
                    <div style="text-align:right; font-size:12px; color:#16A34A; margin-top:5px;">Ahorro: {format_euro(total-deal)}</div>
                </div>
                """, unsafe_allow_html=True)
                st.button("Copiar Oferta Pack", use_container_width=True)

else:
    # PANTALLA DE BIENVENIDA
    st.markdown("""
    <div style="text-align:center; padding:50px; color:#64748B;">
        <h3>Seleccione un cliente para comenzar</h3>
        <p>Utilice la barra lateral para buscar por nombre, ID o filtrar por segmentos estratégicos.</p>
    </div>
    """, unsafe_allow_html=True)
# --- 7. AURA CHATBOT ---
# --- AURA INTEGRATION ---
render_aura(context="Cross Selling IA. El usuario busca oportunidades de venta cruzada, recomendaciones de productos complementarios (bolsos + accesorios) y reglas de asociación.")