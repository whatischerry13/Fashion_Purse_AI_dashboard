import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
import re
from pathlib import Path
# --- IMPORTAR AURA ---
try:
    from src.ui.aura_component import render_aura
except ImportError:
    pass
# 1. Importar common (que ya incluye el path root)
from src.ui.common import setup_page_config, get_project_root, load_data

# 2. Configurar página + Cargar Aura (Todo en una línea)
setup_page_config(page_title="Pricing Lab", layout="wide")

# --- FIX DE RUTAS ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.ui.common import load_data

st.set_page_config(page_title="AI Segmentation Lab", layout="wide")

# --- CSS PREMIUM (Strict Corporate V5.0) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* TOOLTIP */
    .tooltip-container {
        position: relative;
        display: inline-block;
        cursor: default;
        color: #94A3B8;
        margin-left: 6px;
        font-size: 14px;
    }
    .tooltip-container .tooltip-text {
        visibility: hidden;
        width: 250px;
        background-color: #1E293B;
        color: #fff;
        text-align: left;
        border-radius: 4px;
        padding: 12px;
        position: absolute;
        z-index: 100;
        bottom: 125%;
        left: 50%;
        margin-left: -125px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 11px;
        font-weight: 400;
        line-height: 1.5;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        pointer-events: none;
    }
    .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }
    
    /* METRIC CARDS */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 24px;
        border-left: 4px solid #0F172A;
        height: 100%;
    }
    .metric-label { font-size: 11px; color: #64748B; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; display: flex; align-items: center; }
    .metric-value { font-size: 26px; font-weight: 700; color: #0F172A; margin-top: 8px; margin-bottom: 4px; }
    .metric-desc { font-size: 13px; color: #64748B; font-weight: 500; }
    
    /* SIMULATOR BOX */
    .sim-box {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #CBD5E1; border-radius: 8px; padding: 20px;
        margin-bottom: 30px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .sim-result { font-size: 20px; font-weight: 700; color: #16A34A; }
    
    /* STRATEGY CARDS */
    .strategy-box {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px; border-radius: 6px;
        margin-top: 15px; border-left: 4px solid #3B82F6;
        transition: all 0.2s;
    }
    .strategy-box:hover { border-color: #94A3B8; }
    .strategy-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #F1F5F9; padding-bottom: 10px; }
    .strategy-title { font-weight: 700; color: #1E293B; font-size: 15px; }
    .strategy-meta { font-size: 11px; font-weight: 600; color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 4px; }
    
    .strategy-row { display: flex; margin-bottom: 8px; align-items: baseline; }
    .strategy-label { font-weight: 600; color: #0F172A; width: 80px; font-size: 12px; text-transform: uppercase; }
    .strategy-content { color: #334155; font-size: 14px; flex: 1; line-height: 1.5; }
    
    h1, h2, h3 { color: #0F172A; font-family: 'Inter', sans-serif; font-weight: 700; letter-spacing: -0.02em; }
    div[data-testid="stDataFrame"] { width: 100%; border: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)

# --- FORMATO EURO ---
def format_euro(val):
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

# --- LIMPIEZA DE DATOS (NO EMOJIS) ---
def clean_segment_name(name):
    if not isinstance(name, str): return "Desconocido"
    # Mapping estricto a nombres corporativos
    mapping = {
        'Top VIC (Elite)': 'Elite VIC',
        'Retornadores Seriales': 'Riesgo (Devoluciones)',
        'Smart Shoppers (Accesorios)': 'Smart Shoppers',
        'Durmientes / Inactivos': 'Inactivos',
        'Brand Lovers (Fieles)': 'Fidelizados',
        'Standard / Nuevos': 'Standard',
        'Nuevo / Sin Data': 'Sin Histórico'
    }
    for key, val in mapping.items():
        if key in name: return val
    # Fallback: eliminar caracteres no ascii
    clean = name.encode('ascii', 'ignore').decode('ascii').strip()
    return clean if clean else name

def load_cluster_data():
    try:
        clusters_path = project_root / 'data/processed/clients_clusters.csv'
        if clusters_path.exists():
            df = pd.read_csv(clusters_path)
            df['Segmento_Clean'] = df['Segmento_IA'].apply(clean_segment_name)
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None

df_clusters = load_cluster_data()

# --- INTERFAZ PRINCIPAL ---

st.title("AI Segmentation Lab")
st.markdown("Análisis de clustering no supervisado para detección de patrones de comportamiento y oportunidades de ingresos.")

if df_clusters is None or df_clusters.empty:
    st.warning("Datos de segmentación no disponibles.")
    st.stop()

# --- 1. SIMULADOR DE OPORTUNIDAD (NUEVO VALOR ESTRATÉGICO) ---
with st.container():
    st.markdown("### Simulador de Impacto Financiero")
    st.markdown("""
    <div style="font-size:14px; color:#64748B; margin-bottom:15px;">
    Calcula el retorno potencial de activar segmentos específicos basado en su Ticket Medio actual.
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        # Lógica del Simulador
        valid_segments = [s for s in df_clusters['Segmento_Clean'].unique() if s != 'Sin Histórico']
        
        c_sim1, c_sim2, c_sim3 = st.columns([1, 1, 1])
        
        with c_sim1:
            target_seg = st.selectbox("Segmento Objetivo", sorted(valid_segments), index=sorted(valid_segments).index('Inactivos') if 'Inactivos' in valid_segments else 0)
        
        with c_sim2:
            conversion_rate = st.slider("Tasa de Conversión Estimada (%)", 1, 50, 5)
            
        # Cálculos
        seg_data = df_clusters[df_clusters['Segmento_Clean'] == target_seg]
        n_clients = len(seg_data)
        avg_ticket = seg_data['Avg_Ticket'].mean()
        potential_revenue = n_clients * (conversion_rate / 100) * avg_ticket
        
        with c_sim3:
            st.markdown(f"""
            <div class="sim-box">
                <div style="font-size:12px; text-transform:uppercase; color:#64748B; font-weight:700;">Oportunidad Mensual</div>
                <div class="sim-result">{format_euro(potential_revenue)}</div>
                <div style="font-size:12px; color:#475569; margin-top:5px;">
                    Activando a <b>{int(n_clients * conversion_rate/100)}</b> clientes de este grupo.
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- 2. KPIS GLOBALES ---
c1, c2, c3, c4 = st.columns(4)

total_clients = len(df_clusters)
active_clusters = df_clusters['Segmento_Clean'].nunique()
vic_count = len(df_clusters[df_clusters['Segmento_Clean'].str.contains("Elite", case=False, na=False)])
risk_count = len(df_clusters[df_clusters['Segmento_Clean'].str.contains("Riesgo", case=False, na=False)])

def metric_card_html(label, value, desc, tooltip_text, border_color="#0F172A"):
    return f"""
    <div class="metric-card" style="border-left-color: {border_color};">
        <div class="metric-label">
            {label}
            <div class="tooltip-container">?
                <span class="tooltip-text">{tooltip_text}</span>
            </div>
        </div>
        <div class="metric-value">{value}</div>
        <div class="metric-desc">{desc}</div>
    </div>
    """

with c1:
    st.markdown(metric_card_html("Base Analizada", total_clients, "Clientes totales", 
                                 "Total de registros únicos procesados por el algoritmo K-Means."), unsafe_allow_html=True)
with c2:
    st.markdown(metric_card_html("Grupos de Comportamiento", active_clusters, "Clusters IA", 
                                 "Número de patrones diferenciados encontrados matemáticamente."), unsafe_allow_html=True)
with c3:
    st.markdown(metric_card_html("Elite VIC", vic_count, "Alto Valor Neto", 
                                 "Clientes en el percentil superior de Gasto y Frecuencia con baja devolución."), unsafe_allow_html=True)
with c4:
    st.markdown(metric_card_html("Riesgo Operativo", risk_count, "Alerta de Margen", 
                                 "Clientes cuya tasa de devolución erosiona la rentabilidad (>30%).", "#DC2626"), unsafe_allow_html=True)

# --- 3. VISUALIZACIÓN PROFUNDA ---
st.write("")
st.write("")
tab_3d, tab_radar, tab_action = st.tabs(["Mapa Espacial 3D", "Análisis de ADN (Radar)", "Plan de Acción"])

color_map = {
    'Elite VIC': '#0F172A',
    'Riesgo (Devoluciones)': '#DC2626',
    'Smart Shoppers': '#F59E0B',
    'Inactivos': '#94A3B8',
    'Fidelizados': '#EC4899',
    'Standard': '#3B82F6',
    'Sin Histórico': '#E2E8F0'
}

# --- TAB 1: 3D SPACE ---
with tab_3d:
    col_viz, col_legend = st.columns([3, 1])
    
    with col_viz:
        # Filtro de ruido (Sin Gasto)
        df_3d = df_clusters[df_clusters['Monetary'] > 0].copy()
        safe_color_map = {k: v for k, v in color_map.items() if k in df_3d['Segmento_Clean'].unique()}
        
        fig_3d = px.scatter_3d(
            df_3d,
            x='Recency', y='Frequency', z='Monetary',
            color='Segmento_Clean', color_discrete_map=safe_color_map,
            hover_name='Name',
            hover_data={'Client_ID': True, 'Avg_Ticket': ':.2f', 'Segmento_Clean': False},
            labels={'Recency': 'Inactividad (Días)', 'Frequency': 'Frecuencia Compras', 'Monetary': 'LTV (€)'},
            opacity=0.8, size_max=12, height=550
        )
        fig_3d.update_layout(
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(
                xaxis=dict(backgroundcolor="#F8FAFC", gridcolor="#E2E8F0", title_font=dict(size=11, color="#64748B")),
                yaxis=dict(backgroundcolor="#F8FAFC", gridcolor="#E2E8F0", title_font=dict(size=11, color="#64748B")),
                zaxis=dict(backgroundcolor="#F8FAFC", gridcolor="#E2E8F0", title_font=dict(size=11, color="#64748B")),
            ),
            legend=dict(x=0, y=1, title=None, bgcolor="rgba(255,255,255,0.8)")
        )
        st.plotly_chart(fig_3d, use_container_width=True)
    
    with col_legend:
        st.markdown("#### Variables del Modelo")
        st.markdown("""
        <div style="font-size:13px; color:#475569; line-height:1.8;">
        <b>Eje X: Inactividad</b><br>Días desde la última transacción. <br><i>(Derecha = Mayor riesgo de abandono)</i><br><br>
        <b>Eje Y: Frecuencia</b><br>Número de compras realizadas. <br><i>(Arriba = Mayor lealtad)</i><br><br>
        <b>Eje Z: Valor</b><br>Facturación histórica total. <br><i>(Profundidad = Mayor LTV)</i>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 2: RADAR CHART ---
with tab_radar:
    c_radar_controls, c_radar_chart = st.columns([1, 3])
    
    with c_radar_controls:
        st.markdown("#### Comparativa de Perfiles")
        valid_segments = [s for s in sorted(list(df_clusters['Segmento_Clean'].unique())) if s != 'Sin Histórico']
        
        default_sel = []
        if 'Elite VIC' in valid_segments: default_sel.append('Elite VIC')
        if 'Riesgo (Devoluciones)' in valid_segments: default_sel.append('Riesgo (Devoluciones)')
        if not default_sel: default_sel = valid_segments[:2]
        
        selected_radar = st.multiselect("Comparar Segmentos", valid_segments, default=default_sel)
        st.caption("Selecciona segmentos para visualizar sus diferencias estructurales.")
    
    with c_radar_chart:
        if selected_radar:
            numeric_cols = ['Recency', 'Frequency', 'Monetary', 'Avg_Ticket', 'Return_Rate', 'Brand_Loyalty']
            cluster_means = df_clusters.groupby('Segmento_Clean')[numeric_cols].mean().reset_index()
            
            normalized_df = cluster_means.copy()
            for col in numeric_cols:
                min_val = cluster_means[col].min()
                max_val = cluster_means[col].max()
                if max_val > min_val:
                    normalized_df[col] = (cluster_means[col] - min_val) / (max_val - min_val)
                else:
                    normalized_df[col] = 0.5
            
            plot_data = normalized_df[normalized_df['Segmento_Clean'].isin(selected_radar)]
            plot_data_melt = plot_data.melt(id_vars='Segmento_Clean', var_name='Metric', value_name='Score')
            safe_color_map = {k: v for k, v in color_map.items() if k in selected_radar}

            fig_radar = px.line_polar(
                plot_data_melt, r='Score', theta='Metric', color='Segmento_Clean', 
                line_close=True, color_discrete_map=safe_color_map, markers=True
            )
            fig_radar.update_traces(fill='toself', opacity=0.2, line_width=2)
            fig_radar.update_layout(
                height=500,
                polar=dict(radialaxis=dict(visible=True, range=[0, 1], showticklabels=False), bgcolor="#FFFFFF"),
                margin=dict(t=30, b=30),
                legend=dict(orientation="h", y=-0.1, title=None)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

# --- TAB 3: STRATEGY ---
with tab_action:
    st.markdown("#### Recomendaciones Tácticas (IA)")
    
    strategies = {
        'Elite VIC': {
            'Obj': 'Retención Absoluta',
            'Acc': 'Asignación de Concierge y Pre-Order.',
            'Ch': 'WhatsApp Directo',
            'Why': 'Generan el 80% del margen neto.'
        },
        'Riesgo (Devoluciones)': {
            'Obj': 'Protección de Margen',
            'Acc': 'Exclusión de envíos gratuitos. Bloqueo de ofertas.',
            'Ch': 'Email Transaccional',
            'Why': 'Coste logístico excede el beneficio.'
        },
        'Smart Shoppers': {
            'Obj': 'Elevación de Ticket',
            'Acc': 'Bundles de producto y financiación.',
            'Ch': 'Retargeting / Ads',
            'Why': 'Alta frecuencia, bajo valor unitario.'
        },
        'Inactivos': {
            'Obj': 'Reactivación (Win-Back)',
            'Acc': 'Oferta agresiva por tiempo limitado.',
            'Ch': 'Email / SMS',
            'Why': 'Riesgo inminente de pérdida definitiva.'
        },
        'Fidelizados': {
            'Obj': 'Embajadores',
            'Acc': 'Programa de referidos.',
            'Ch': 'App / Email',
            'Why': 'Alta lealtad de marca.'
        },
        'Standard': {
            'Obj': 'Hábito de Compra',
            'Acc': 'Nurturing educativo sobre marca.',
            'Ch': 'Email Secuencial',
            'Why': 'Necesitan educación para repetir.'
        },
        'Sin Histórico': {
            'Obj': 'Primera Conversión',
            'Acc': 'Incentivo de bienvenida.',
            'Ch': 'Email',
            'Why': 'Leads en fase de consideración.'
        }
    }
    
    col_a, col_b = st.columns(2) # Layout en 2 columnas para ser más compacto
    
    # Repartir tarjetas
    segments = sorted(list(df_clusters['Segmento_Clean'].unique()))
    mid_point = len(segments) // 2 + 1
    
    for i, segment in enumerate(segments):
        strat = strategies.get(segment, {'Obj': 'Revisión', 'Acc': 'Manual', 'Ch': 'General', 'Why': 'Sin datos'})
        seg_stats = df_clusters[df_clusters['Segmento_Clean'] == segment]
        avg_ticket = seg_stats['Avg_Ticket'].mean()
        count = len(seg_stats)
        border_color = color_map.get(segment, "#E2E8F0")
        
        # Asignar a columna
        target_col = col_a if i < mid_point else col_b
        
        with target_col:
            st.markdown(f"""
            <div class="strategy-box" style="border-left-color: {border_color};">
                <div class="strategy-header">
                    <div class="strategy-title" style="color:{border_color}; margin:0;">{segment}</div>
                    <div class="strategy-meta">{count} Clientes | AOV: {format_euro(avg_ticket)}</div>
                </div>
                <div class="strategy-row">
                    <div class="strategy-label">Objetivo</div>
                    <div class="strategy-content">{strat['Obj']}</div>
                </div>
                <div class="strategy-row">
                    <div class="strategy-label">Acción</div>
                    <div class="strategy-content">
                        {strat['Acc']}
                        <div class="tooltip-container">?
                            <span class="tooltip-text">Razón Estratégica: {strat['Why']}</span>
                        </div>
                    </div>
                </div>
                <div class="strategy-row">
                    <div class="strategy-label">Canal</div>
                    <div class="strategy-content">{strat['Ch']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
# --- 7. AURA CHATBOT ---
# --- AURA INTEGRATION ---
render_aura(context="Segmentación IA. El usuario analiza clusters de clientes agrupados por comportamiento (RFM), demografía y patrones de compra predictivos.")