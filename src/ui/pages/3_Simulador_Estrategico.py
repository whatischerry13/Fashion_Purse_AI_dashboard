import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
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

st.set_page_config(page_title="Simulador Estratégico", layout="wide")

# --- CSS PREMIUM ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Tarjetas KPI de Impacto */
    .impact-card {
        background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 20px;
        text-align: center; transition: all 0.2s;
    }
    .impact-label { font-size: 0.8rem; color: #64748B; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .impact-value { font-size: 1.6rem; color: #0F172A; font-weight: 700; }
    .impact-delta { font-size: 0.9rem; font-weight: 600; margin-top: 5px; }
    
    /* Colores Delta */
    .positive { color: #16A34A; }
    .negative { color: #DC2626; }
    .neutral { color: #64748B; }
    
    /* Títulos de Panel */
    .panel-header {
        background-color: #F1F5F9; 
        border-left: 4px solid #0F172A; 
        padding: 10px 15px; 
        border-radius: 0 4px 4px 0;
        margin-bottom: 20px;
        color: #0F172A;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.9rem;
    }
    
    .section-title { font-size: 1.1rem; font-weight: 700; color: #1E293B; margin-top: 30px; margin-bottom: 15px; border-bottom: 2px solid #F1F5F9; padding-bottom: 5px; }
    
    /* Executive Box */
    .exec-summary-box {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #2563EB;
        border-radius: 6px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .exec-title { font-size: 1rem; font-weight: 700; color: #0F172A; margin-bottom: 10px; text-transform: uppercase; }
    .exec-text { font-size: 0.95rem; color: #475569; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# --- HELPER: FORMATO EURO ---
def format_euro(val):
    return f"{val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

# --- LÓGICA DE SIMULACIÓN ---
def run_simulation(df_base, mkt_boost_pct, comp_aggressiveness):
    df_sim = df_base.copy()
    mkt_factor = 1 + ((mkt_boost_pct / 100) * 0.6)
    comp_map = {"Baja": 1.05, "Media": 1.0, "Alta": 0.92, "Guerra de Precios": 0.85}
    comp_factor = comp_map.get(comp_aggressiveness, 1.0)
    
    df_sim['Prediccion_Realista'] = df_sim['Prediccion_Realista'] * mkt_factor * comp_factor
    
    base_mkt_budget = df_base['Prediccion_Realista'].sum() * 0.15
    extra_mkt_cost = base_mkt_budget * (mkt_boost_pct / 100)
    
    return df_sim, extra_mkt_cost, base_mkt_budget

# --- CARGA ---
db = load_data()
df_forecast = db.get('forecast')

# --- SIDEBAR LIMPIO ---
with st.sidebar:
    st.markdown("### HERAS PURSE AI")
    st.caption("Intelligence Suite V25")
    
    if df_forecast is not None:
        cluster_map = {
            'High_End': 'High End (Hermès, Chanel)', 
            'Standard': 'Standard (Gucci, Prada)'
        }
        rev_map = {v: k for k, v in cluster_map.items()}
        ui_opts = [cluster_map.get(c, c) for c in df_forecast['Cluster'].unique()]
        sel_ui = st.selectbox("Unidad de Negocio", ui_opts)
        sel_cluster = rev_map.get(sel_ui, sel_ui)
    else:
        st.error("Sin datos.")
        st.stop()

# --- DATOS BASE ---
df_base = df_forecast[df_forecast['Cluster'] == sel_cluster].copy()

# --- CALLBACK DE RESETEO (LA MAGIA) ---
def reset_values():
    st.session_state['mkt_slider'] = 0
    st.session_state['comp_slider'] = "Media"

# --- INTERFAZ ---
st.title("Simulador de Escenarios Estratégicos")
st.markdown("""
<div style='color:#64748B; margin-bottom:20px;'>
Proyección de impacto financiero basada en palancas de crecimiento y amenazas competitivas.
</div>
""", unsafe_allow_html=True)

# 1. PANEL DE CONTROL
c_controls, c_kpis = st.columns([1, 2])

with c_controls:
    st.markdown('<div class="panel-header">Palancas de Negocio</div>', unsafe_allow_html=True)
    
    # Inicializar valores en session_state si no existen
    if 'mkt_slider' not in st.session_state: st.session_state['mkt_slider'] = 0
    if 'comp_slider' not in st.session_state: st.session_state['comp_slider'] = "Media"
    
    # Sliders CON KEY para controlarlos
    mkt_boost = st.slider("Boost Inversión Marketing", 0, 100, key="mkt_slider", format="%d%%", help="Incremento sobre presupuesto base.")
    comp_level = st.select_slider("Agresividad Competencia", options=["Baja", "Media", "Alta", "Guerra de Precios"], key="comp_slider")
    
    st.write("") 
    # El botón llama a la función de callback
    st.button("Restablecer Valores", use_container_width=True, on_click=reset_values)

# 2. CÁLCULOS
df_sim, extra_cost, base_budget = run_simulation(df_base, mkt_boost, comp_level)

base_rev = df_base['Prediccion_Realista'].sum()
sim_rev = df_sim['Prediccion_Realista'].sum()
delta_rev = sim_rev - base_rev

gross_margin = delta_rev * 0.60
net_impact = gross_margin - extra_cost

with c_kpis:
    k1, k2, k3 = st.columns(3)
    
    color_rev = "positive" if delta_rev >= 0 else "negative"
    k1.markdown(f"""
    <div class="impact-card">
        <div class="impact-label">Ingresos Proyectados</div>
        <div class="impact-value">{format_euro(sim_rev)}</div>
        <div class="impact-delta {color_rev}">{"+" if delta_rev>0 else ""}{format_euro(delta_rev)}</div>
    </div>""", unsafe_allow_html=True)
    
    k2.markdown(f"""
    <div class="impact-card">
        <div class="impact-label">Coste Extra Marketing</div>
        <div class="impact-value" style="color:#DC2626;">-{format_euro(extra_cost)}</div>
        <div class="impact-delta neutral">Inversión Adicional</div>
    </div>""", unsafe_allow_html=True)
    
    roi_color = "positive" if net_impact > 0 else "negative"
    k3.markdown(f"""
    <div class="impact-card" style="border-top: 4px solid {'#16A34A' if net_impact>0 else '#DC2626'};">
        <div class="impact-label">Impacto en Beneficio</div>
        <div class="impact-value">{"+" if net_impact>0 else ""}{format_euro(net_impact)}</div>
        <div class="impact-delta {roi_color}">{"RENTABLE" if net_impact>0 else "NO RENTABLE"}</div>
    </div>""", unsafe_allow_html=True)

# 3. GRÁFICO COMPARATIVO
st.markdown('<div class="section-title">Análisis de Desviación (Baseline vs Simulación)</div>', unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_base['Fecha'], y=df_base['Prediccion_Realista'],
    name='Forecast Base', line=dict(color='#94A3B8', width=2, dash='dash')
))
fig.add_trace(go.Scatter(
    x=df_sim['Fecha'], y=df_sim['Prediccion_Realista'],
    name='Escenario Simulado', line=dict(color='#2563EB', width=4)
))
fig.add_trace(go.Scatter(
    x=pd.concat([df_base['Fecha'], df_base['Fecha'][::-1]]),
    y=pd.concat([df_sim['Prediccion_Realista'], df_base['Prediccion_Realista'][::-1]]),
    fill='toself', fillcolor='rgba(34, 197, 94, 0.2)' if delta_rev > 0 else 'rgba(220, 38, 38, 0.2)',
    line=dict(color='rgba(0,0,0,0)'), name='Gap', hoverinfo="skip"
))
fig.update_layout(
    template="plotly_white", height=400, legend=dict(orientation="h", y=1.1),
    separators=",.", yaxis=dict(title="Ingresos (€)"), hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

# 4. WATERFALL (PUENTE DE INGRESOS)
st.markdown('<div class="section-title">Desglose de Impacto Financiero</div>', unsafe_allow_html=True)

c_water, c_summary = st.columns([2, 1])

with c_water:
    impact_mkt = base_rev * ((mkt_boost / 100) * 0.6)
    rev_after_mkt = base_rev + impact_mkt
    comp_factor = {"Baja": 1.05, "Media": 1.0, "Alta": 0.92, "Guerra de Precios": 0.85}.get(comp_level, 1.0)
    impact_comp = (rev_after_mkt * comp_factor) - rev_after_mkt
    
    max_val = max(base_rev, sim_rev, rev_after_mkt)
    
    fig_water = go.Figure(go.Waterfall(
        name="Bridge", orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Forecast Base", "Efecto Marketing", "Impacto Competencia", "Forecast Final"],
        textposition="outside",
        text=[format_euro(val) for val in [base_rev, impact_mkt, impact_comp, sim_rev]],
        y=[base_rev, impact_mkt, impact_comp, 0],
        connector={"line":{"color":"rgb(63, 63, 63)"}},
        decreasing={"marker":{"color":"#DC2626"}},
        increasing={"marker":{"color":"#16A34A"}},
        totals={"marker":{"color":"#0F172A"}}
    ))
    fig_water.update_layout(
        title="Puente de Ingresos (Revenue Bridge)",
        template="plotly_white", height=400, separators=",.",
        yaxis=dict(range=[0, max_val * 1.25]), margin=dict(t=60)
    )
    st.plotly_chart(fig_water, use_container_width=True)

with c_summary:
    if net_impact > 0:
        title_dg = "Escenario Favorable"
        msg = "El incremento de ventas cubre el coste de marketing adicional. Se recomienda proceder si el flujo de caja lo permite."
    elif net_impact > -5000:
        title_dg = "Escenario Neutral"
        msg = "El beneficio neto apenas varía. Estrategia válida solo para ganar cuota de mercado (Branding) pero no rentabilidad."
    else:
        title_dg = "Escenario Negativo"
        msg = "La inversión destruye valor. El coste de adquisición marginal supera el margen bruto generado."

    st.markdown(f"""
    <div class="exec-summary-box">
        <div class="exec-title">Diagnóstico de la IA</div>
        <div class="exec-text">
            <b>{title_dg}</b>
            <br>{msg}
            <br><br>
            <ul>
                <li><b>Elasticidad:</b> 0.6 (Saturación de canal).</li>
                <li><b>Margen Bruto:</b> Estimado al 60%.</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
# --- AURA INTEGRATION ---
render_aura(context="Simulador Estratégico. El usuario está ejecutando escenarios 'What-If', proyectando resultados financieros y ajustando palancas de negocio para ver impactos futuros.")