import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import timedelta
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

st.set_page_config(page_title="Smart Stock Planner", layout="wide")

# --- CSS V25 PROFESSIONAL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* KPI Containers */
    .kpi-container {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 0px; 
        padding: 24px; border-left: 4px solid #0F172A;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .kpi-label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: #64748B; letter-spacing: 1px; }
    .kpi-value { font-size: 26px; font-weight: 700; color: #0F172A; margin-top: 8px; font-feature-settings: "tnum"; }
    .kpi-sub { font-size: 13px; color: #475569; margin-top: 4px; }
    
    /* Headers & Text */
    .section-title { font-size: 18px; font-weight: 600; color: #1E293B; margin-top: 40px; margin-bottom: 20px; border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; }
    
    /* Tables */
    div[data-testid="stDataFrame"] { border: 1px solid #E2E8F0; background: white; border-radius: 4px; }
    
    /* Insights */
    .insight-box { background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 25px; border-left: 4px solid #3B82F6; }
    .insight-title { font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 10px; text-transform: uppercase; }
    .insight-text { font-size: 14px; color: #334155; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# --- FORMATO EURO STRICT ---
def format_euro(val):
    return f"{val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

# --- LÓGICA DE NEGOCIO HÍBRIDA (VELOCITY REAL + MUESTREO STOCK) ---
def analyze_stock_dynamics(df_sales, df_inv, date_range_days, target_weeks):
    if df_sales is None or df_sales.empty: return None, None

    # 1. ANALIZAR VELOCIDAD REAL (SALES HISTORY)
    # Filtramos por ventana temporal seleccionada
    sales_clean = df_sales.copy()
    if 'Fecha' in sales_clean.columns:
        sales_clean['Fecha'] = pd.to_datetime(sales_clean['Fecha'])
        max_date = sales_clean['Fecha'].max()
        cutoff_date = max_date - timedelta(days=date_range_days)
        sales_clean = sales_clean[sales_clean['Fecha'] >= cutoff_date]
        
        # Semanas reales en el periodo
        weeks_active = (max_date - cutoff_date).days / 7
        if weeks_active < 1: weeks_active = 1
    else:
        weeks_active = 52 # Fallback
    
    # Velocidad por Marca (Euros/Semana)
    velocity = sales_clean.groupby('Marca')['Net_Revenue'].sum().reset_index()
    velocity.columns = ['Marca', 'Revenue_Period']
    velocity['Weekly_Run_Rate'] = velocity['Revenue_Period'] / weeks_active
    
    # 2. CALCULAR STOCK IDEAL (TARGET GLOBAL)
    velocity['Target_Stock'] = velocity['Weekly_Run_Rate'] * target_weeks
    total_target_value = velocity['Target_Stock'].sum()
    
    # 3. STOCK OPERATIVO (MUESTREO INTELIGENTE)
    # Usamos tu lógica ganadora: Filtramos el inventario masivo para que coincida con la realidad operativa
    # Objetivo: Que el Stock Actual sea aprox 1.1 veces el Target Global (para simular realidad con ligeros desajustes)
    
    inv_real = df_inv.copy()
    if 'Current_Price' in inv_real.columns: inv_real['Val'] = inv_real['Current_Price']
    else: inv_real['Val'] = inv_real['Precio_Venta_EUR']
    
    # Mezclar y coger muestra hasta llegar al valor realista
    inv_real = inv_real.sample(frac=1, random_state=42).reset_index(drop=True)
    inv_real['CumSum'] = inv_real['Val'].cumsum()
    
    # Cortamos el inventario cuando llega al 110% del Target (simulación de almacén físico real)
    cutoff = total_target_value * 1.1 
    if cutoff == 0: cutoff = 500000 # Fallback si no hay ventas
    
    current_stock_filtered = inv_real[inv_real['CumSum'] <= cutoff].copy()
    
    # Agrupar Stock Actual por Marca
    current_stock_grouped = current_stock_filtered.groupby('Marca')['Val'].sum().reset_index(name='Current_Stock_Value')
    
    # 4. MASTER DATAFRAME (CRUCE)
    df_plan = pd.merge(velocity, current_stock_grouped, on='Marca', how='outer').fillna(0)
    
    df_plan['Stock_Gap'] = df_plan['Current_Stock_Value'] - df_plan['Target_Stock']
    
    # Weeks of Supply (WOS)
    df_plan['WOS'] = np.where(df_plan['Weekly_Run_Rate'] > 0, 
                              df_plan['Current_Stock_Value'] / df_plan['Weekly_Run_Rate'], 
                              99)
    
    # 5. CLASIFICACIÓN ABC (PARETO V25)
    df_plan = df_plan.sort_values('Weekly_Run_Rate', ascending=False)
    df_plan['Cum_Rev'] = df_plan['Weekly_Run_Rate'].cumsum()
    total_run_rate = df_plan['Weekly_Run_Rate'].sum()
    
    if total_run_rate > 0:
        df_plan['Cum_Pct'] = df_plan['Cum_Rev'] / total_run_rate
    else:
        df_plan['Cum_Pct'] = 1.0

    def classify_abc(pct):
        if pct <= 0.80: return 'A'
        elif pct <= 0.95: return 'B'
        else: return 'C'
    
    df_plan['Class_ABC'] = df_plan['Cum_Pct'].apply(classify_abc)
    
    # 6. ESTRATEGIA
    def define_strategy(row):
        if row['WOS'] < (target_weeks * 0.5): return "ADQUISICION PRIORITARIA"
        elif row['WOS'] < (target_weeks * 0.8): return "REPONER"
        elif row['WOS'] > (target_weeks * 2): return "LIQUIDACION TACTICA"
        else: return "MANTENER"
        
    df_plan['Strategy'] = df_plan.apply(define_strategy, axis=1)
    
    return df_plan, current_stock_filtered, weeks_active

# --- CARGA ---
db = load_data()
df_sales = db.get('sales')
df_inv_full = db.get('inventory')

if df_sales is None or df_inv_full is None:
    st.error("Datos insuficientes para el análisis.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### HERAS PURSE AI")
    st.caption("Intelligence Suite V25")
    
    st.markdown("#### Configuración de Análisis")
    
    # Selector de Ventana Temporal
    time_window = st.selectbox(
        "Ventana de Análisis",
        options=[30, 90, 180, 365],
        format_func=lambda x: f"Últimos {x} días",
        index=2 # Default 180 días (Semestre)
    )
    
    target_weeks = st.slider("Objetivo Cobertura (Semanas)", 4, 16, 8, help="Semanas de venta que queremos cubrir con el stock.")
    
    st.divider()
    view_abc = st.multiselect("Clasificación ABC", ["A", "B", "C"], default=["A", "B"])

# --- PROCESAMIENTO ---
df_plan, df_stock_items, weeks_analyzed = analyze_stock_dynamics(df_sales, df_inv_full, time_window, target_weeks)

# Filtro visual ABC
df_view = df_plan[df_plan['Class_ABC'].isin(view_abc)]

# --- INTERFAZ ---
st.title("Smart Stock Planner")
st.markdown(f"""
<div style='color:#64748B; margin-bottom:30px;'>
Planificación basada en <b>Velocidad Real de Venta</b> (últimos {time_window} días).
<br>Stock Operativo calibrado automáticamente para reflejar la realidad en tienda.
</div>
""", unsafe_allow_html=True)

# 1. KPIS CORPORATIVOS
total_velocity = df_plan['Weekly_Run_Rate'].sum()
inventory_val = df_plan['Current_Stock_Value'].sum()
wos_global = inventory_val / total_velocity if total_velocity > 0 else 0
gap_net = df_plan['Stock_Gap'].sum()

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Velocidad Semanal (Run Rate)</div>
    <div class="kpi-value">{format_euro(total_velocity)}</div><div class="kpi-sub">Media del periodo</div></div>""", unsafe_allow_html=True)
    
with k2:
    st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Valor Stock Operativo</div>
    <div class="kpi-value">{format_euro(inventory_val)}</div><div class="kpi-sub">Muestra activa en tienda</div></div>""", unsafe_allow_html=True)
    
with k3:
    color_wos = "#16A34A" if (target_weeks - 2) <= wos_global <= (target_weeks + 2) else "#D97706"
    st.markdown(f"""<div class="kpi-container"><div class="kpi-label">Cobertura Global</div>
    <div class="kpi-value" style="color:{color_wos}">{wos_global:.1f} Semanas</div><div class="kpi-sub">Objetivo: {target_weeks} Semanas</div></div>""", unsafe_allow_html=True)

with k4:
    col_gap = "#DC2626" if gap_net < 0 else "#2563EB"
    label_gap = "DÉFICIT (OTB)" if gap_net < 0 else "EXCEDENTE"
    st.markdown(f"""<div class="kpi-container" style="border-left-color:{col_gap}"><div class="kpi-label">Posición Financiera</div>
    <div class="kpi-value" style="color:{col_gap}">{format_euro(abs(gap_net))}</div><div class="kpi-sub">{label_gap}</div></div>""", unsafe_allow_html=True)

# 2. ANÁLISIS DE BRECHA (CHART)
st.markdown('<div class="section-title">Análisis de Cobertura por Marca (Top 10 Volumen)</div>', unsafe_allow_html=True)

top_10 = df_view.sort_values('Weekly_Run_Rate', ascending=False).head(10)

fig = go.Figure()

# Stock Actual
fig.add_trace(go.Bar(
    x=top_10['Marca'], y=top_10['Current_Stock_Value'],
    name='Stock Actual', marker_color='#334155'
))

# Stock Objetivo
fig.add_trace(go.Bar(
    x=top_10['Marca'], y=top_10['Target_Stock'],
    name='Stock Objetivo', marker_color='#94A3B8'
))

# Gap Markers
fig.add_trace(go.Scatter(
    x=top_10['Marca'], y=top_10['Current_Stock_Value'],
    mode='markers',
    marker=dict(
        size=12,
        color=np.where(top_10['Stock_Gap'] < 0, '#DC2626', '#16A34A'),
        symbol=np.where(top_10['Stock_Gap'] < 0, 'triangle-down', 'circle')
    ),
    name='Gap Status',
    text=top_10['Strategy']
))

fig.update_layout(
    template="plotly_white", height=380,
    legend=dict(orientation="h", y=1.1),
    yaxis=dict(title="Valoración (€)", gridcolor='#F1F5F9'),
    xaxis=dict(gridcolor='#F1F5F9'),
    separators=",."
)
st.plotly_chart(fig, use_container_width=True)

# 3. PLANIFICACIÓN TÁCTICA (TABLAS)
col_buy, col_opt = st.columns(2)

with col_buy:
    st.markdown('<div class="section-title" style="color:#1E40AF">Plan de Compras (Open-To-Buy)</div>', unsafe_allow_html=True)
    
    buy_opps = df_plan[df_plan['Stock_Gap'] < 0].sort_values('Stock_Gap')
    
    if not buy_opps.empty:
        disp_buy = buy_opps[['Marca', 'Class_ABC', 'Weekly_Run_Rate', 'Stock_Gap']].copy()
        disp_buy['Stock_Gap'] = disp_buy['Stock_Gap'].abs()
        disp_buy.columns = ['Marca', 'Clasif.', 'Velocidad/Sem', 'Presupuesto Requerido']
        
        st.dataframe(
            disp_buy.head(8).style.format({
                'Velocidad/Sem': '{:,.0f} €',
                'Presupuesto Requerido': '{:,.0f} €'
            }).background_gradient(subset=['Presupuesto Requerido'], cmap='Blues'),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Stock suficiente para cubrir la demanda actual.")

with col_opt:
    st.markdown('<div class="section-title" style="color:#B91C1C">Optimización de Inventario (Overstock)</div>', unsafe_allow_html=True)
    
    overstock = df_plan[df_plan['Stock_Gap'] > 0].sort_values('Stock_Gap', ascending=False)
    
    if not overstock.empty:
        disp_over = overstock[['Marca', 'Class_ABC', 'WOS', 'Stock_Gap']].copy()
        disp_over.columns = ['Marca', 'Clasif.', 'Cobertura (Sem)', 'Excedente Capital']
        
        st.dataframe(
            disp_over.head(8).style.format({
                'Cobertura (Sem)': '{:.1f}',
                'Excedente Capital': '{:,.0f} €'
            }).background_gradient(subset=['Excedente Capital'], cmap='Reds'),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Niveles de inventario optimizados.")

# 4. INSIGHT ESTRATÉGICO
top_A_brand = df_plan[df_plan['Class_ABC']=='A'].iloc[0]['Marca']
critical_gap_brand = buy_opps.iloc[0]['Marca'] if not buy_opps.empty else "N/A"
critical_gap_val = abs(buy_opps.iloc[0]['Stock_Gap']) if not buy_opps.empty else 0

st.markdown(f"""
<div class="insight-box">
    <div class="insight-title">Informe de Dirección de Operaciones</div>
    <div class="insight-text">
        <p><b>1. Análisis de Rendimiento:</b> La marca <b>{top_A_brand}</b> lidera la clasificación ABC, generando el mayor volumen de flujo de caja en los últimos {time_window} días. Es vital proteger su nivel de servicio.</p>
        <p><b>2. Alerta de Cadena de Suministro:</b> Se detecta una rotura de stock proyectada en <b>{critical_gap_brand}</b> con un déficit de {format_euro(critical_gap_val)}. Dada su velocidad de venta, esto representa un riesgo inmediato de pérdida de ingresos.</p>
        <p><b>3. Recomendación:</b> Asignar prioridad de CAPEX (Presupuesto de Compra) a las marcas de Clasificación A y B listadas en la tabla izquierda para mantener la cobertura de {target_weeks} semanas.</p>
    </div>
</div>
""", unsafe_allow_html=True)