import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta
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

st.set_page_config(page_title="Analisis Macro & Prediccion", layout="wide")

# --- CSS PROFESSIONAL (CLEAN) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    .kpi-card {
        background-color: white; border: 1px solid #E2E8F0; border-radius: 6px; padding: 15px;
        margin-bottom: 10px; border-left: 3px solid #0F172A; transition: all 0.3s ease;
    }
    .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .kpi-value { font-size: 22px; font-weight: 700; color: #0F172A; margin: 2px 0; }
    .kpi-label { font-size: 11px; color: #64748B; font-weight: 600; text-transform: uppercase; }
    .kpi-delta { font-size: 11px; font-weight: 600; margin-top: 4px; }
    .positive { color: #16A34A; }
    .negative { color: #DC2626; }
    
    .chart-title { font-size: 14px; font-weight: 700; color: #334155; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;}
    .stSlider { padding-top: 0px; margin-top: -20px; }
    
    /* Insight Box Pro */
    .insight-box {
        background-color: #FFFFFF; border-radius: 8px; padding: 20px; margin-top: 15px;
        border: 1px solid #E2E8F0; border-left: 4px solid #3B82F6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .insight-header { font-size: 14px; font-weight: 700; color: #1E3A8A; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;}
    .insight-body { font-size: 14px; color: #334155; line-height: 1.6; }
    .insight-recommendation { margin-top: 12px; padding-top: 12px; border-top: 1px dashed #CBD5E1; font-size: 13px; font-weight: 600; color: #0F172A; }
    
    /* Badge de Estado */
    .status-badge {
        display: inline-block; padding: 4px 10px; border-radius: 4px; 
        font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .badge-history { background-color: #E2E8F0; color: #475569; }
    .badge-forecast { background-color: #DBEAFE; color: #1E40AF; }
</style>
""", unsafe_allow_html=True)

# --- CARGA DATOS ---
try:
    db = load_data()
    df_raw = db.get('macro')
    # Cargamos la predicción real de ventas para alimentar el modelo macro
    try:
        df_sales_forecast = pd.read_csv(project_root / 'data/processed/forecast_horizon.csv')
    except:
        df_sales_forecast = pd.DataFrame()
except Exception as e:
    st.error(f"Error sistema: {e}")
    st.stop()

if df_raw is None or df_raw.empty:
    st.warning("Datos macroeconómicos no disponibles.")
    st.stop()

# --- MOTOR DE SIMULACIÓN HÍBRIDO (DATA-BACKED) ---
def get_seasonality_factor(month):
    """Factor estacional base del sector lujo (Respaldo empírico general)"""
    map_season = {
        1: 0.9, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.05, 6: 1.0,
        7: 0.95, 8: 0.9, 9: 1.1, 10: 1.0, 11: 1.2, 12: 1.3
    }
    return map_season.get(month, 1.0)

def extend_with_data_driven_forecast(df, df_sales, horizon_months=14):
    """
    Proyecta el futuro combinando:
    1. Economía: Inercia de los últimos datos reales (Regresión Lineal local).
    2. Hype: Correlacionado con nuestra propia predicción de ventas (forecast_horizon.csv).
    """
    df = df.copy()
    if 'Fecha' not in df.columns: return df
    
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df = df.sort_values('Fecha').dropna(subset=['Fecha'])
    
    last_date = df['Fecha'].max()
    last_eco = df['Economic_Index'].iloc[-1]
    last_hype = df['Luxury_Hype'].iloc[-1]
    
    # 1. Calcular tendencia económica reciente (Slope)
    if len(df) >= 3:
        recent_eco = df['Economic_Index'].tail(6).values
        x = np.arange(len(recent_eco))
        slope, _ = np.polyfit(x, recent_eco, 1)
    else:
        slope = 0
    
    # Preparar fechas futuras
    future_dates = [last_date + timedelta(days=30*i) for i in range(1, horizon_months+1)]
    future_eco = []
    future_hype = []
    
    # Preprocesar Sales Forecast si existe
    has_sales_data = False
    if not df_sales.empty and 'ds' in df_sales.columns and 'yhat' in df_sales.columns:
        df_sales['ds'] = pd.to_datetime(df_sales['ds'])
        has_sales_data = True

    # Semilla para consistencia en el componente aleatorio residual
    np.random.seed(42)
    
    current_eco = last_eco
    
    for date in future_dates:
        # A. ECONOMÍA: Proyección Inercial
        # La economía tiene inercia, no cambia de golpe. Proyectamos la pendiente atenuada.
        current_eco += slope
        slope *= 0.95 # La tendencia se debilita con el tiempo (incertidumbre)
        # Añadimos ruido micro (shocks económicos leves)
        noise = np.random.normal(0, 0.005)
        future_eco.append(current_eco + noise)
        
        # B. HYPE: Data-Driven por Predicción de Ventas
        hype_val = last_hype # Base
        
        if has_sales_data:
            # Buscamos si hay predicción de ventas para ese mes/año
            # Usamos una ventana de tolerancia de 15 días
            mask = (df_sales['ds'] - date).abs() < timedelta(days=15)
            if mask.any():
                sales_pred = df_sales[mask]['yhat'].iloc[0]
                # Normalizamos: ¿Cuánto es esta venta respecto a la media?
                # Si vendemos mucho, el Hype es alto.
                sales_avg = df_sales['yhat'].mean()
                sales_factor = sales_pred / sales_avg if sales_avg > 0 else 1.0
                
                # Ajustamos el Hype base por el factor de ventas predicho
                # Factor de amortiguación 0.5 para que el Hype no sea tan volátil como las ventas puras
                hype_val = last_hype * (0.5 + 0.5 * sales_factor)
            else:
                # Fallback: Estacionalidad Genérica si no hay dato de venta exacto
                hype_val = current_eco * get_seasonality_factor(date.month)
        else:
            # Fallback Total: Economía * Estacionalidad
            hype_val = current_eco * get_seasonality_factor(date.month)
            
        future_hype.append(hype_val)

    df_future = pd.DataFrame({
        'Fecha': future_dates,
        'Economic_Index': future_eco,
        'Luxury_Hype': future_hype,
        'Tipo': 'Previsión (IA)'
    })
    
    df['Tipo'] = 'Histórico'
    return pd.concat([df, df_future], ignore_index=True)

# Preparar Datos Completos
df_full = extend_with_data_driven_forecast(df_raw, df_sales_forecast)
df_full['Fecha_Str'] = df_full['Fecha'].dt.strftime('%Y-%m-%d')
df_full = df_full.sort_values('Fecha').reset_index(drop=True)

# --- LAYOUT PRINCIPAL ---

st.title("Macro Intelligence Hub")
st.markdown("Análisis de indicadores externos respaldado por datos históricos y modelos predictivos.")

# 1. SLIDER MAESTRO
fechas_disponibles = df_full['Fecha_Str'].tolist()
# Default: Último dato histórico
last_hist_idx = df_full[df_full['Tipo'] == 'Histórico'].index.max()
default_date = df_full.iloc[last_hist_idx]['Fecha_Str']

selected_date_str = st.select_slider(
    "Línea de Tiempo (Desliza para ver la predicción basada en ventas)",
    options=fechas_disponibles,
    value=default_date,
    label_visibility="collapsed"
)

# Datos Actuales
curr_idx = df_full[df_full['Fecha_Str'] == selected_date_str].index[0]
current_data = df_full.iloc[curr_idx]
prev_data = df_full.iloc[curr_idx - 1] if curr_idx > 0 else current_data
is_forecast = current_data['Tipo'] == 'Previsión (IA)'

# Badge
badge_class = "badge-forecast" if is_forecast else "badge-history"
badge_text = "PROYECCION IA" if is_forecast else "DATO HISTORICO"

st.markdown(f"""
<div style="margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
    <span class="status-badge {badge_class}">{badge_text}</span>
    <span style="font-size: 14px; color: #64748B;">Fecha de Análisis: <b>{selected_date_str}</b></span>
</div>
""", unsafe_allow_html=True)

# 2. GRÁFICO EVOLUCIÓN
fig_trend = go.Figure()

# Histórico
mask_hist = df_full['Tipo'] == 'Histórico'
fig_trend.add_trace(go.Scatter(
    x=df_full[mask_hist]['Fecha'], y=df_full[mask_hist]['Economic_Index'],
    name='Economía (Real)', mode='lines', line=dict(color='#0F172A', width=2),
    fill='tozeroy', fillcolor='rgba(15, 23, 42, 0.05)'
))
fig_trend.add_trace(go.Scatter(
    x=df_full[mask_hist]['Fecha'], y=df_full[mask_hist]['Luxury_Hype'],
    name='Hype (Real)', mode='lines', line=dict(color='#DC2626', width=2)
))

# Previsión
mask_fore = df_full['Tipo'] == 'Previsión (IA)'
if mask_fore.any():
    last_hist = df_full[mask_hist].iloc[-1:]
    df_fore_plot = pd.concat([last_hist, df_full[mask_fore]])
    
    fig_trend.add_trace(go.Scatter(
        x=df_fore_plot['Fecha'], y=df_fore_plot['Economic_Index'],
        name='Economía (IA)', mode='lines', line=dict(color='#0F172A', width=2, dash='dot')
    ))
    fig_trend.add_trace(go.Scatter(
        x=df_fore_plot['Fecha'], y=df_fore_plot['Luxury_Hype'],
        name='Hype (IA)', mode='lines', line=dict(color='#DC2626', width=2, dash='dot')
    ))

# Cursor Vertical
fig_trend.add_vline(x=current_data['Fecha'], line_width=1, line_color="black")

# Zona Futura
if mask_fore.any():
    start_forecast = df_full[mask_fore]['Fecha'].min()
    end_forecast = df_full[mask_fore]['Fecha'].max()
    fig_trend.add_vrect(
        x0=start_forecast, x1=end_forecast,
        fillcolor="rgba(59, 130, 246, 0.05)", layer="below", line_width=0,
        annotation_text="Horizonte Predictivo", annotation_position="top left"
    )

fig_trend.update_layout(
    template="plotly_white", height=300, margin=dict(l=20, r=20, t=10, b=20),
    hovermode="x unified", legend=dict(orientation="h", y=1.1, x=0),
    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#F1F5F9')
)
st.plotly_chart(fig_trend, use_container_width=True)

# 3. SPLIT INFERIOR
c_left, c_right = st.columns([1.3, 1])

with c_left:
    st.markdown('<div class="chart-title">Indicadores Clave</div>', unsafe_allow_html=True)
    k1, k2 = st.columns(2)
    
    metrics = [("Índice Económico", "Economic_Index", " pts"), ("Demanda Lujo (Hype)", "Luxury_Hype", " pts")]
    
    for col, (label, col_name, suffix) in zip([k1, k2], metrics):
        val = current_data[col_name]
        prev = prev_data[col_name]
        delta = val - prev
        pct = ((val - prev) / abs(prev)) * 100 if prev != 0 else 0
        
        is_positive = delta >= 0
        color_cls = "positive" if is_positive else "negative"
        sign = "+" if is_positive else ""
        
        with col:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{val:,.2f}{suffix}</div><div class="kpi-delta {color_cls}">{sign}{delta:.2f} ({sign}{pct:.1f}%)</div></div>""", unsafe_allow_html=True)

    # GENERADOR DE INSIGHTS
    seasonality_factor = get_seasonality_factor(current_data['Fecha'].month)
    
    rec_text = ""
    if seasonality_factor > 1.15:
        rec_text = "<b>Alerta de Temporada Alta:</b> Nuestros modelos de ventas anticipan un pico de demanda. Estrategia: Maximizar margen y reducir descuentos."
    elif seasonality_factor < 0.95:
        rec_text = "<b>Valle Estacional:</b> Periodo de baja actividad proyectada. Recomendamos acciones de fidelización para mantener rotación."
    else:
        rec_text = "<b>Estabilidad:</b> El mercado se comporta según la media anual. Buen momento para probar nuevos canales."

    insight_source = "Cruzando datos con el Forecast de Ventas interno..." if is_forecast else "Datos históricos consolidados."

    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-header">Analista de Mercado (IA)</div>
        <div class="insight-body">
            {insight_source} Para la fecha seleccionada, detectamos un comportamiento típico del mes de <b>{current_data['Fecha'].strftime('%B')}</b>.
            El índice de Hype se sitúa en <b>{current_data['Luxury_Hype']:.2f}</b>, alineado con la proyección de ingresos.
        </div>
        <div class="insight-recommendation">{rec_text}</div>
    </div>
    """, unsafe_allow_html=True)

with c_right:
    st.markdown('<div class="chart-title" style="text-align:center;">Matriz de Oportunidad</div>', unsafe_allow_html=True)
    
    # AJUSTE DE EJES DINÁMICO (CORRECCIÓN SOLICITADA)
    # Calculamos min/max globales con un margen del 10%
    x_min, x_max = df_full['Economic_Index'].min(), df_full['Economic_Index'].max()
    y_min, y_max = df_full['Luxury_Hype'].min(), df_full['Luxury_Hype'].max()
    margin_x = (x_max - x_min) * 0.1
    margin_y = (y_max - y_min) * 0.1
    
    fig_matrix = px.scatter(
        df_full, x='Economic_Index', y='Luxury_Hype',
        color='Luxury_Hype', color_continuous_scale='RdBu_r',
        labels={'Economic_Index': 'Economía', 'Luxury_Hype': 'Hype'},
        opacity=0.4
    )
    
    # Punto Actual
    fig_matrix.add_trace(go.Scatter(
        x=[current_data['Economic_Index']], y=[current_data['Luxury_Hype']],
        mode='markers',
        marker=dict(color='#16A34A', size=20, symbol='circle', line=dict(width=3, color='white')),
        name='Actual', hoverinfo='skip'
    ))
    
    fig_matrix.update_layout(
        template="plotly_white", height=320,
        margin=dict(l=20, r=20, t=10, b=20),
        # Ejes dinámicos para que no se vea pequeño
        xaxis=dict(showgrid=True, gridcolor='#F1F5F9', range=[x_min - margin_x, x_max + margin_x]), 
        yaxis=dict(showgrid=True, gridcolor='#F1F5F9', range=[y_min - margin_y, y_max + margin_y]),
        showlegend=False, coloraxis_showscale=False
    )
    
    st.plotly_chart(fig_matrix, use_container_width=True)
# --- 7. AURA CHATBOT ---
# --- AURA INTEGRATION ---
render_aura(context="Análisis Macroeconómico. El usuario revisa indicadores globales, inflación, tendencias del sector lujo internacional y factores externos que afectan la demanda.")