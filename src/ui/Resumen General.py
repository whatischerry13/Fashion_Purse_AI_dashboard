import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os
from pathlib import Path

# --- 1. BLINDAJE DE ARRANQUE EN FRÍO (OBLIGATORIO AQUÍ) ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# ----------------------------------------------------------

# --- 2. IMPORTACIONES ---
try:
    from src.ui.common import load_data
    # AQUÍ ESTÁ LA MAGIA: Importamos el componente visual de Aura
    from src.ui.aura_component import render_aura 
except ModuleNotFoundError:
    st.rerun()

# --- 3. CONFIGURACIÓN ---
st.set_page_config(page_title="Resumen General", layout="wide")

# Estilos CSS (Sin cambios, para tus tablas y KPIs)
st.markdown("""
<style>
    .stApp { font-family: 'Helvetica Neue', sans-serif; background-color: #FFFFFF; }
    .kpi-container {
        border-left: 4px solid #0F172A; background-color: #F8FAFC; padding: 15px;
        border-radius: 0px 8px 8px 0px; margin-bottom: 10px;
    }
    .kpi-label { font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase; }
    .kpi-value { font-size: 1.8rem; color: #0F172A; font-weight: 700; margin-top: 5px; }
    .kpi-sub { font-size: 0.9rem; margin-top: 2px; }
    .custom-box { padding: 15px; border-radius: 6px; margin-bottom: 20px; font-size: 0.95rem; }
    .box-info { background-color: #F1F5F9; color: #475569; border-left: 4px solid #94A3B8; }
    div[data-testid="stDataFrame"] { width: 100%; }
    .stChatInput { padding-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

def format_euro(val):
    return f"{val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

try:
    db = load_data()
except Exception:
    st.error("Error conectando a datos.")
    st.stop()

# --- SIDEBAR (Solo Filtros) ---
with st.sidebar:
    st.markdown("### HERAS PURSE AI")
    st.caption("Intelligence Suite V25")
    if 'forecast' in db and not db['forecast'].empty:
        df_forecast = db['forecast']
        cluster_map = {'High_End': 'High End (Hermès, Chanel)', 'Standard': 'Standard (Gucci, Prada)'}
        rev_map = {v: k for k, v in cluster_map.items()}
        ui_opts = [cluster_map.get(c, c) for c in df_forecast['Cluster'].unique()]
        sel_ui = st.selectbox("Unidad de Negocio", ui_opts)
        sel_key = rev_map.get(sel_ui, sel_ui)
        st.session_state['global_cluster'] = sel_key
        data = df_forecast[df_forecast['Cluster'] == sel_key].copy()
        avg_risk = data['Riesgo_Score'].mean() if 'Riesgo_Score' in data.columns else 0
    else:
        st.error("Sistema Offline."); st.stop()

# ==============================================================================
# LAYOUT PRINCIPAL (Dashboard Izquierda - Aura Derecha)
# ==============================================================================

col_dash, col_aura = st.columns([3, 1])

# --- COLUMNA 1: DASHBOARD FINANCIERO (Tu código intacto) ---
with col_dash:
    st.title(f"Forecast Financiero: {sel_ui}")
    st.markdown("<div style='color: #64748B; margin-bottom: 20px;'>Vision consolidada del rendimiento esperado.</div>", unsafe_allow_html=True)
    st.markdown("---")

    # KPIs
    tot_sales = data['Prediccion_Realista'].sum()
    max_sales = data['Escenario_Optimista'].sum()
    upside = max_sales - tot_sales
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Ingresos Proyectados</div><div class="kpi-value">{format_euro(tot_sales)}</div><div class="kpi-sub">Escenario Base</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-container" style="border-left-color: #22C55E;"><div class="kpi-label">Oportunidad Alcista</div><div class="kpi-value">{format_euro(upside)}</div><div class="kpi-sub" style="color: #16A34A;">Potencial Upside</div></div>""", unsafe_allow_html=True)
    risk_col = "#DC2626" if avg_risk > 40 else "#EAB308" if avg_risk > 20 else "#16A34A"
    with c3:
        st.markdown(f"""<div class="kpi-container" style="border-left-color: {risk_col};"><div class="kpi-label">Exposicion al Riesgo</div><div class="kpi-value" style="color: {risk_col};">{avg_risk:.1f}%</div><div class="kpi-sub" style="color: {risk_col};">Volatilidad a la baja</div></div>""", unsafe_allow_html=True)

    # Gráfico Anual
    st.subheader("Curva de Tendencia Anual")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pd.concat([data['Fecha'], data['Fecha'][::-1]]), y=pd.concat([data['Escenario_Optimista'], data['Escenario_Pesimista'][::-1]]), fill='toself', fillcolor='rgba(226, 232, 240, 0.5)', line=dict(color='rgba(0,0,0,0)'), name='Rango'))
    fig.add_trace(go.Scatter(x=data['Fecha'], y=data['Prediccion_Realista'], line=dict(color='#0F172A', width=3), name='Objetivo'))
    fig.update_layout(template="plotly_white", margin=dict(t=10, b=0, l=0, r=0), height=350, legend=dict(orientation="h", y=1.1), separators=",.")
    st.plotly_chart(fig, use_container_width=True)

    # Análisis Semanal
    st.markdown("---")
    st.subheader("Analisis Semanal")
    col_sel, col_chart = st.columns([1, 3])
    with col_sel:
        data['Semana_Label'] = data['Fecha'].dt.strftime('%d %b %Y')
        selected_week_label = st.selectbox("Semana:", data['Semana_Label'].tolist())
        week_data = data[data['Semana_Label'] == selected_week_label].iloc[0]
        st.markdown(f"""<div class="custom-box box-info"><b>Semana {selected_week_label}</b><br><br>Target: {format_euro(week_data['Prediccion_Realista'])}<br>Riesgo: {week_data['Riesgo_Score']:.1f}%</div>""", unsafe_allow_html=True)
    with col_chart:
        fig_week = go.Figure()
        fig_week.add_trace(go.Bar(x=['Min', 'Target', 'Max'], y=[week_data['Escenario_Pesimista'], week_data['Prediccion_Realista'], week_data['Escenario_Optimista']], marker_color=['#94A3B8', '#0F172A', '#16A34A'], text=[format_euro(v) for v in [week_data['Escenario_Pesimista'], week_data['Prediccion_Realista'], week_data['Escenario_Optimista']]], textposition='auto'))
        fig_week.update_layout(template="plotly_white", height=300, margin=dict(t=40, b=0, l=0, r=0), separators=",.")
        st.plotly_chart(fig_week, use_container_width=True)

    # Tabla
    with st.expander("Ver Tabla Completa"):
        st.dataframe(data[['Fecha', 'Prediccion_Realista', 'Escenario_Pesimista', 'Escenario_Optimista', 'Riesgo_Score']], use_container_width=True, column_config={"Prediccion_Realista": st.column_config.NumberColumn("Objetivo", format="%.0f €")})

# --- COLUMNA 2: AURA (LA ÚNICA LÍNEA QUE NECESITAS AHORA) ---
with col_aura:
    # Llamamos al componente y le decimos qué está viendo el usuario
    render_aura(context=f"El usuario ve el Dashboard de {sel_ui}. Riesgo actual: {avg_risk:.1f}%")