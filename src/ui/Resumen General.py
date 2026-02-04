import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

# --- 1. MAGIC PATH FIX (ESTO VA LO PRIMERO DE TODO) ---
# Esto es necesario para que encuentre 'src' y 'render_aura'
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# -----------------------------------------------------

# --- IMPORTACIONES ---
try:
    from src.ui.common import setup_page_config, load_data
    from src.rag.engine import LuxuryAssistant
    # IMPORTAMOS EL COMPONENTE DE AURA QUE CREAMOS ANTES
    from src.ui.aura_component import render_aura 
except ModuleNotFoundError:
    st.rerun()

# Configuración de página (Una sola vez)
st.set_page_config(page_title="Resumen General", layout="wide")

# ==============================================================================
# ZONA DE DIAGNÓSTICO PROFUNDO (TU CÓDIGO ORIGINAL)
# ==============================================================================
st.divider()
st.subheader("🕵️‍♂️ Diagnóstico Técnico de Aura")

try:
    # 1. Intentamos importar el cerebro
    st.write("✅ Importación del módulo: CORRECTA")
    
    # 2. Intentamos iniciar el cerebro
    st.write("⏳ Intentando iniciar LuxuryAssistant...")
    # Usamos st.cache_resource si está disponible, si no, instanciamos directo para el test
    test_aura = LuxuryAssistant()
    
    # 3. Verificamos si se crearon las piezas internas
    if hasattr(test_aura, 'vector_db'):
        st.success("✅ Base de Datos Vectorial: CARGADA")
    else:
        st.error("❌ Base de Datos: FALLÓ (No se creó self.vector_db)")

    if hasattr(test_aura, 'chain'):
        st.success("✅ Cadena de Razonamiento: CARGADA")
    else:
        st.error("❌ Cadena: FALLÓ (No se creó self.chain)")
        
except Exception as e:
    st.error("💥 ERROR CRÍTICO DETECTADO:")
    st.code(str(e))
    import traceback
    st.code(traceback.format_exc())

# ==============================================================================
# TU CÓDIGO DE DISEÑO Y GRÁFICOS (INTACTO)
# ==============================================================================

# --- ESTILOS CSS PREMIUM ---
st.markdown("""
<style>
    .stApp { font-family: 'Helvetica Neue', sans-serif; background-color: #FFFFFF; }
    
    .kpi-container {
        border-left: 4px solid #0F172A;
        background-color: #F8FAFC;
        padding: 15px;
        border-radius: 0px 8px 8px 0px;
        transition: transform 0.2s;
        cursor: default;
        margin-bottom: 10px;
    }
    .kpi-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .kpi-label { font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-value { font-size: 1.8rem; color: #0F172A; font-weight: 700; margin-top: 5px; }
    .kpi-sub { font-size: 0.9rem; margin-top: 2px; }
    
    .custom-box { padding: 15px; border-radius: 6px; margin-bottom: 20px; font-size: 0.95rem; }
    .box-info { background-color: #F1F5F9; color: #475569; border-left: 4px solid #94A3B8; }
    
    div[data-testid="stDataFrame"] { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- HELPER: FORMATO EURO ESPAÑA ---
def format_euro(val):
    """Ej: 1200 -> 1.200 €"""
    return f"{val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

# Carga de Datos
try:
    db = load_data()
except Exception:
    st.error("Error cargando datos.")
    st.stop()

# --- SIDEBAR LIMPIO ---
with st.sidebar:
    st.markdown("### HERAS PURSE AI")
    st.caption("Intelligence Suite V25")
    
    if 'forecast' in db and not db['forecast'].empty:
        df_forecast = db['forecast']
        
        # MAPEO DE NOMBRES
        cluster_map = {
            'High_End': 'High End (Hermès, Chanel)', 
            'Standard': 'Standard (Gucci, Prada)'
        }
        rev_map = {v: k for k, v in cluster_map.items()}
        
        ui_opts = [cluster_map.get(c, c) for c in df_forecast['Cluster'].unique()]
        sel_ui = st.selectbox("Unidad de Negocio", ui_opts)
        
        sel_key = rev_map.get(sel_ui, sel_ui)
        st.session_state['global_cluster'] = sel_key
        
        data = df_forecast[df_forecast['Cluster'] == sel_key].copy()
        avg_risk = data['Riesgo_Score'].mean() if 'Riesgo_Score' in data.columns else 0
    else:
        st.error("Sistema Offline.")
        st.stop()

# --- TÍTULO ---
st.title(f"Forecast Financiero: {sel_ui}")
st.markdown("""
<div style='color: #64748B; margin-bottom: 20px;'>
Vision consolidada del rendimiento esperado para las proximas 52 semanas.
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# 1. KPIs (CON FORMATO EURO)
tot_sales = data['Prediccion_Realista'].sum()
max_sales = data['Escenario_Optimista'].sum()
upside = max_sales - tot_sales

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="kpi-container" title="Suma total de ventas estimadas (Modelo de Regresion Cuantilica - Mediana).">
        <div class="kpi-label">Ingresos Proyectados</div>
        <div class="kpi-value">{format_euro(tot_sales)}</div>
        <div class="kpi-sub" style="color: #64748B;">Escenario Base</div>
    </div>
    """, unsafe_allow_html=True)
    
with c2:
    st.markdown(f"""
    <div class="kpi-container" style="border-left-color: #22C55E;" title="Diferencial positivo capturable bajo condiciones de mercado optimas.">
        <div class="kpi-label">Oportunidad Alcista</div>
        <div class="kpi-value">{format_euro(upside)}</div>
        <div class="kpi-sub" style="color: #16A34A;">Potencial Upside</div>
    </div>
    """, unsafe_allow_html=True)
    
risk_col = "#DC2626" if avg_risk > 40 else "#EAB308" if avg_risk > 20 else "#16A34A"
with c3:
    st.markdown(f"""
    <div class="kpi-container" style="border-left-color: {risk_col};" title="Proporcion de ingresos expuestos a volatilidad negativa de mercado.">
        <div class="kpi-label">Exposicion al Riesgo</div>
        <div class="kpi-value" style="color: {risk_col};">{avg_risk:.1f}%</div>
        <div class="kpi-sub" style="color: {risk_col};">Volatilidad a la baja</div>
    </div>
    """, unsafe_allow_html=True)

st.caption("**Definicion de Exposicion al Riesgo:** Metrica de sensibilidad que cuantifica el porcentaje de ingresos no garantizados ante un escenario de contraccion de demanda.")

# 2. GRÁFICO DE TENDENCIA (PLOTLY ESPAÑOLIZADO)
st.subheader("Curva de Tendencia Anual")
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=pd.concat([data['Fecha'], data['Fecha'][::-1]]),
    y=pd.concat([data['Escenario_Optimista'], data['Escenario_Pesimista'][::-1]]),
    fill='toself', fillcolor='rgba(226, 232, 240, 0.5)', 
    line=dict(color='rgba(0,0,0,0)'), name='Rango de Incertidumbre'
))
fig.add_trace(go.Scatter(
    x=data['Fecha'], y=data['Prediccion_Realista'], 
    line=dict(color='#0F172A', width=3), name='Forecast Objetivo'
))
fig.update_layout(
    template="plotly_white", margin=dict(t=10, b=0, l=0, r=0), height=350, 
    legend=dict(orientation="h", y=1.1),
    separators=",." # Magia para decimales con coma y miles con punto en ejes
)
st.plotly_chart(fig, use_container_width=True)

# 3. ANÁLISIS SEMANAL (CON FORMATO)
st.markdown("---")
st.subheader("Analisis de Profundidad Semanal")
st.markdown("Seleccione una semana especifica para auditar la horquilla de precios exacta.")

col_sel, col_chart = st.columns([1, 3])

with col_sel:
    data['Semana_Label'] = data['Fecha'].dt.strftime('%d %b %Y')
    selected_week_label = st.selectbox("Seleccionar Semana:", data['Semana_Label'].tolist())
    week_data = data[data['Semana_Label'] == selected_week_label].iloc[0]
    
    st.markdown(f"""
    <div class="custom-box box-info">
        <b>Detalle Semana {selected_week_label}</b><br><br>
        <b>Suelo (Min):</b> {format_euro(week_data['Escenario_Pesimista'])}<br>
        <b>Objetivo:</b> {format_euro(week_data['Prediccion_Realista'])}<br>
        <b>Techo (Max):</b> {format_euro(week_data['Escenario_Optimista'])}<br><br>
        <b>Riesgo:</b> {week_data['Riesgo_Score']:.1f}%
    </div>
    """, unsafe_allow_html=True)

with col_chart:
    fig_week = go.Figure()
    fig_week.add_trace(go.Bar(
        x=['Pesimista', 'Realista', 'Optimista'],
        y=[week_data['Escenario_Pesimista'], week_data['Prediccion_Realista'], week_data['Escenario_Optimista']],
        marker_color=['#94A3B8', '#0F172A', '#16A34A'],
        text=[format_euro(val) for val in [week_data['Escenario_Pesimista'], week_data['Prediccion_Realista'], week_data['Escenario_Optimista']]],
        textposition='auto',
    ))
    fig_week.update_layout(
        title=f"Horquilla de Escenarios: Semana del {selected_week_label}",
        template="plotly_white", height=300, yaxis_title="Volumen de Ventas (€)", margin=dict(t=40, b=0, l=0, r=0),
        separators=",."
    )
    st.plotly_chart(fig_week, use_container_width=True)

# 4. TABLA COMPLETA (FORMATO D3 PARA PUNTOS Y COMAS)
with st.expander("Ver Tabla de Datos Completa"):
    st.markdown("Pase el cursor sobre los titulos para ver las definiciones tecnicas.")
    st.dataframe(
        data[['Fecha', 'Prediccion_Realista', 'Escenario_Pesimista', 'Escenario_Optimista', 'Riesgo_Score']],
        use_container_width=True,
        column_config={
            "Fecha": st.column_config.DateColumn("Semana Fiscal", format="DD MMM YYYY", help="Fecha de inicio del periodo."),
            "Prediccion_Realista": st.column_config.NumberColumn("Objetivo (Target)", format="%.0f €", help="Proyeccion central de ingresos."),
            "Escenario_Pesimista": st.column_config.NumberColumn("Suelo (Min)", format="%.0f €", help="Limite inferior (Worst Case)."),
            "Escenario_Optimista": st.column_config.NumberColumn("Techo (Max)", format="%.0f €", help="Limite superior (Best Case)."),
            "Riesgo_Score": st.column_config.ProgressColumn("Indice de Riesgo", format="%.1f%%", min_value=0, max_value=100, help="Probabilidad de desviacion negativa.")
        }
    )

# ==============================================================================
# AQUÍ ESTÁ LA INTEGRACIÓN DE AURA (BURBUJA FLOTANTE)
# ==============================================================================
render_aura(context=f"Usuario viendo Forecast de {sel_ui}. Riesgo: {avg_risk:.1f}%")