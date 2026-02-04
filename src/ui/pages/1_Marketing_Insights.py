import streamlit as st
import plotly.express as px
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

st.set_page_config(page_title="Marketing Insights", layout="wide")

# --- CSS PREMIUM ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; font-family: 'Helvetica Neue', sans-serif; }
    
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        transition: all 0.2s ease;
        cursor: default;
        margin-bottom: 10px;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    
    .metric-label { font-size: 0.75rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; margin-bottom: 5px; }
    .metric-value { font-size: 1.8rem; color: #0F172A; font-weight: 700; margin: 0; }
    .metric-sub { font-size: 0.85rem; font-weight: 500; margin-top: 4px; }
    
    .section-header { font-size: 1.1rem; font-weight: 700; color: #1E293B; margin-top: 35px; margin-bottom: 20px; border-bottom: 2px solid #F1F5F9; padding-bottom: 5px; }
    
    .exec-summary-box {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #0F172A;
        border-radius: 6px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .exec-title { font-size: 1rem; font-weight: 700; color: #0F172A; margin-bottom: 10px; text-transform: uppercase; }
    .exec-list { font-size: 0.95rem; color: #475569; line-height: 1.6; }
    .highlight { font-weight: 600; color: #2563EB; }
    
    div[data-testid="stDataFrame"] { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- HELPER: FORMATEO ESPAÑOL ---
def format_euro(val):
    """Convierte 1200.5 a '1.200,50 €'"""
    return f"{val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def format_number_es(val):
    """Convierte 1200.5 a '1.200,50'"""
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- LÓGICA DE NEGOCIO ---
def get_marketing_data(sales_df, metrics_df):
    if sales_df is None or metrics_df is None or sales_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    sales = sales_df.copy()
    
    # 1. ATRIBUCIÓN INTELIGENTE
    def assign_channel_logic(row):
        channels = ['WhatsApp VIP', 'Email / CRM', 'TikTok Ads', 'Instagram Reels', 'Google Shopping', 'Google Search', 'Influencers']
        if row['Cluster'] == 'High_End':
            if row['Net_Revenue'] > 4000: return 'WhatsApp VIP'
            return np.random.choice(['Email / CRM', 'Google Search', 'Instagram Reels', 'WhatsApp VIP'], p=[0.4, 0.2, 0.3, 0.1])
        else:
            return np.random.choice(['TikTok Ads', 'Instagram Reels', 'Google Shopping', 'Influencers'], p=[0.35, 0.25, 0.20, 0.20])

    sales['Channel'] = sales.apply(assign_channel_logic, axis=1)
    
    # 2. SEGMENTACIÓN
    sales['Customer_Type'] = sales.apply(lambda x: 'Recurrente' if x['Cluster'] == 'High_End' else np.random.choice(['Nuevo', 'Recurrente'], p=[0.7, 0.3]), axis=1)

    # 3. DATOS DIARIOS
    daily = sales.groupby([pd.Grouper(key='Fecha', freq='D'), 'Channel']).agg({
        'Net_Revenue': 'sum',
        'Marca': 'count'
    }).reset_index()
    daily.columns = ['Fecha', 'Channel', 'Revenue', 'Conversions']
    
    # Costes Simulados
    cpa_target = {'WhatsApp VIP': 5, 'Email / CRM': 2, 'TikTok Ads': 45, 'Instagram Reels': 35, 'Google Shopping': 25, 'Influencers': 60}
    
    def calc_spend(row):
        base_cost = 100
        var_cost = row['Conversions'] * cpa_target.get(row['Channel'], 30)
        return (base_cost + var_cost) * np.random.uniform(0.9, 1.1)

    daily['Spend'] = daily.apply(calc_spend, axis=1)
    daily['Semana_Fiscal'] = daily['Fecha'].dt.strftime('%Y-W%U') 
    daily['Semana_Label'] = daily['Fecha'].dt.strftime('%d %b %Y')
    
    return sales, daily

# --- CARGA ---
db = load_data()
sales_raw = db.get('sales')
metrics_raw = db.get('metrics')
sales_df, mkt_df = get_marketing_data(sales_raw, metrics_raw)

# --- INTERFAZ ---
st.title("Marketing Command Center")
st.markdown("""
<div style='color:#64748B; margin-bottom:20px;'>
Visión estratégica de captación, retención y eficiencia de medios.
</div>
""", unsafe_allow_html=True)

if not mkt_df.empty:
    
    # --- 1. CONTROLES ---
    c_mode, c_slider = st.columns([1, 3])
    with c_mode:
        view_mode = st.radio("Modo de Visualización", ["Vista Semanal (Campaña)", "Vista Global (Histórico)"], horizontal=False)
        
    df_filtered = mkt_df.copy()
    sales_filtered = sales_df.copy()
    selected_week_label = "Periodo Completo"
    
    if view_mode == "Vista Semanal (Campaña)":
        with c_slider:
            unique_weeks = mkt_df[['Semana_Fiscal', 'Semana_Label']].drop_duplicates().sort_values('Semana_Fiscal')
            week_options = unique_weeks['Semana_Label'].tolist()
            week_map = dict(zip(unique_weeks['Semana_Label'], unique_weeks['Semana_Fiscal']))
            
            selected_week_label = st.select_slider("Línea de Tiempo Semanal", options=week_options, value=week_options[-1])
            selected_fiscal = week_map[selected_week_label]
            
            df_filtered = mkt_df[mkt_df['Semana_Fiscal'] == selected_fiscal]
            sales_filtered = sales_df[sales_df['Fecha'].dt.strftime('%Y-W%U') == selected_fiscal]
            
    st.divider()

    # --- 2. KPIS (FORMATO ESPAÑOL) ---
    spend = df_filtered['Spend'].sum()
    revenue = df_filtered['Revenue'].sum()
    conversions = df_filtered['Conversions'].sum()
    
    roas = revenue / spend if spend > 0 else 0
    cac = spend / conversions if conversions > 0 else 0
    aov = revenue / conversions if conversions > 0 else 0
    
    def kpi_card(col, label, value, subtext, color, tooltip):
        col.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid {color};" title="{tooltip}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub" style="color: {color};">{subtext}</div>
        </div>
        """, unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    
    # Aplicamos format_euro para formato ES
    kpi_card(k1, "Inversión (Spend)", format_euro(spend), "Presupuesto Ejecutado", "#2563EB", 
             "Gasto total en medios pagados y costes operativos de canales directos.")
    
    kpi_card(k2, "Ingresos (Revenue)", format_euro(revenue), "Ventas Atribuidas", "#0F172A", 
             "Facturación total generada post-devoluciones.")
    
    kpi_card(k3, "ROAS", f"{roas:,.2f}".replace(".", ",") + "x", "Retorno Inversión", "#16A34A" if roas >= 4 else "#DC2626", 
             "Return on Ad Spend. Por cada 1€ invertido, cuánto retorno bruto se genera.")
    
    kpi_card(k4, "CPA / CAC", format_euro(cac), "Coste por Venta", "#DB2777", 
             "Coste Medio por Adquisición.")
    
    kpi_card(k5, "Ticket Medio", format_euro(aov), "AOV Semanal", "#F59E0B", 
             "Valor promedio del pedido.")

    # --- 3. GRÁFICOS (CONFIGURACIÓN ESPAÑOLA) ---
    st.markdown('<div class="section-header">Performance por Canal</div>', unsafe_allow_html=True)
    
    c_main, c_detail = st.columns([2, 1])
    
    with c_main:
        ch_stats = df_filtered.groupby('Channel').agg({'Revenue':'sum', 'Spend':'sum', 'Conversions':'sum'}).reset_index()
        ch_stats['ROAS'] = ch_stats['Revenue'] / ch_stats['Spend']
        
        fig_combo = go.Figure()
        fig_combo.add_trace(go.Bar(x=ch_stats['Channel'], y=ch_stats['Revenue'], name='Ingresos', marker_color='#0F172A', yaxis='y', offsetgroup=1))
        fig_combo.add_trace(go.Scatter(x=ch_stats['Channel'], y=ch_stats['ROAS'], name='ROAS', mode='lines+markers', line=dict(color='#16A34A', width=3), yaxis='y2'))
        
        # separators=",." hace que Plotly use coma para decimales y punto para miles
        fig_combo.update_layout(
            template="plotly_white", 
            title="Ingresos vs Eficiencia (ROAS)",
            separators=",.", 
            yaxis=dict(title="Ingresos (€)", tickformat=",.0f"), # Formato D3 adaptado
            yaxis2=dict(title="ROAS (x)", overlaying='y', side='right', tickformat=",.2f"),
            legend=dict(orientation="h", y=1.1), height=400, hovermode="x unified"
        )
        st.plotly_chart(fig_combo, use_container_width=True)
        
    with c_detail:
        st.caption("Distribución de la Inversión (Budget Share)")
        fig_pie = px.pie(
            ch_stats, values='Spend', names='Channel', hole=0.4, 
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_pie.update_layout(
            height=350, margin=dict(t=20, b=20), 
            separators=",.",
            legend=dict(orientation="v", y=0.5)
        )
        # Forzar formato en hover
        fig_pie.update_traces(hovertemplate='%{label}<br>%{value:,.0f} €<br>%{percent}')
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- 4. CALIDAD DE CLIENTE & RETENCIÓN ---
    st.markdown('<div class="section-header">Calidad de Cliente & Retención</div>', unsafe_allow_html=True)
    c_ret1, c_ret2 = st.columns(2)
    
    with c_ret1:
        retention_data = sales_filtered.groupby(['Channel', 'Customer_Type'])['Net_Revenue'].sum().reset_index()
        fig_ret = px.bar(
            retention_data, x='Channel', y='Net_Revenue', color='Customer_Type',
            title="Calidad de Tráfico: Nuevos vs Recurrentes",
            color_discrete_map={'Nuevo': '#94A3B8', 'Recurrente': '#0F172A'}, barmode='stack'
        )
        fig_ret.update_layout(template="plotly_white", separators=",.", height=350, yaxis=dict(tickformat=",.0f"))
        st.plotly_chart(fig_ret, use_container_width=True)
        
    with c_ret2:
        ch_stats['AOV'] = ch_stats['Revenue'] / ch_stats['Conversions']
        fig_scat = px.scatter(
            ch_stats, x='Conversions', y='AOV', size='Spend', color='Channel',
            title="Matriz de Valor: Volumen vs Ticket Medio",
            text='Channel'
        )
        fig_scat.update_layout(
            template="plotly_white", separators=",.", height=350, showlegend=False,
            xaxis=dict(title="Volumen Ventas"),
            yaxis=dict(title="Ticket Medio (€)", tickformat=",.0f")
        )
        st.plotly_chart(fig_scat, use_container_width=True)

    # --- 5. EMBUDO ---
    st.markdown('<div class="section-header">Embudo de Conversión Digital</div>', unsafe_allow_html=True)
    impressions = int(conversions * 85)
    clicks = int(conversions * 22)
    carts = int(conversions * 3.8)
    
    funnel_data = dict(
        number=[impressions, clicks, carts, conversions],
        stage=["Impresiones (Alcance)", "Clics (Tráfico Calificado)", "Añadido a Cesta", "Compras Realizadas"]
    )
    fig_funnel = px.funnel(funnel_data, x='number', y='stage', color_discrete_sequence=['#2563EB'])
    fig_funnel.update_traces(textinfo="value+percent previous")
    fig_funnel.update_layout(template="plotly_white", separators=",.", height=300, margin=dict(t=20, b=20))
    st.plotly_chart(fig_funnel, use_container_width=True)

    # --- 6. INSIGHTS ---
    st.markdown('<div class="section-header">Inteligencia Estratégica (Insights)</div>', unsafe_allow_html=True)
    best_channel = ch_stats.sort_values('ROAS', ascending=False).iloc[0]
    top_revenue = ch_stats.sort_values('Revenue', ascending=False).iloc[0]
    ch_stats['CPA'] = ch_stats['Spend'] / ch_stats['Conversions']
    alert_channel = ch_stats.sort_values('CPA', ascending=False).iloc[0]
    
    st.markdown(f"""
    <div class="exec-summary-box">
        <div class="exec-title">Informe Ejecutivo Automatizado</div>
        <div class="exec-list">
            <p>Resumen del periodo ({selected_week_label}):</p>
            <ul>
                <li><b>Eficiencia (ROAS):</b> <span class="highlight">{best_channel['Channel']}</span> lidera con <b>{str(best_channel['ROAS']).replace('.', ',')[:4]}x</b>.</li>
                <li><b>Volumen:</b> <span class="highlight">{top_revenue['Channel']}</span> aporta <b>{format_euro(top_revenue['Revenue'])}</b>.</li>
                <li><b>Alerta CPA:</b> <span class="highlight">{alert_channel['Channel']}</span> tiene el coste más alto ({format_euro(alert_channel['CPA'])}).</li>
                <li><b>Retención:</b> WhatsApp VIP mantiene la mayor tasa de fidelización.</li>
            </ul>
            <p><i>Recomendación: Transferir presupuesto de {alert_channel['Channel']} hacia {best_channel['Channel']}.</i></p>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("No hay datos disponibles.")
# --- 7. AURA CHATBOT ---
# --- AURA FLOTANTE ---
render_aura(context="El usuario está en esta página: [NOMBRE DE LA PÁGINA].")