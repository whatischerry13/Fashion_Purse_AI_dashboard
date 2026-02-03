import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta, time
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

st.set_page_config(page_title="Client 360 CRM", layout="wide")

# --- INICIALIZACIÓN DE ESTADO (REUNIONES) ---
if 'meetings' not in st.session_state:
    st.session_state.meetings = []

# --- CSS V60 CLEAN CORPORATE ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* TOOLTIP */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: default;
        margin-left: 6px;
        color: #94A3B8;
        font-size: 14px;
        font-style: normal;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 240px;
        background-color: #1E293B;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 100;
        bottom: 130%;
        left: 50%;
        margin-left: -120px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 12px;
        font-weight: 400;
        line-height: 1.4;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

    /* KPIs */
    .kpi-container {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 24px; border-left: 4px solid #0F172A;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .kpi-value { font-size: 28px; font-weight: 700; color: #0F172A; margin-top: 5px; }
    .kpi-label { font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center; }
    
    /* Client Cards */
    .client-card {
        background-color: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px; margin-bottom: 12px;
        transition: transform 0.2s; border-left: 4px solid transparent; cursor: pointer;
    }
    .client-card:hover { transform: translateX(3px); box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .client-name { font-size: 16px !important; font-weight: 700; color: #0F172A; }
    .client-meta { font-size: 13px !important; color: #475569; margin-top: 4px; }
    
    /* Wishlist Match */
    .wish-match {
        background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 15px; margin-top: 15px;
    }
    .wish-title { color: #166534; font-weight: 700; font-size: 14px; }
    
    /* Timeline Pro */
    .timeline-container {
        position: relative; padding-left: 20px; border-left: 2px solid #E2E8F0; margin-top: 10px;
    }
    .timeline-item { position: relative; margin-bottom: 20px; }
    .timeline-item::before {
        content: ''; position: absolute; left: -26px; top: 5px; width: 10px; height: 10px; 
        border-radius: 50%; background: #CBD5E1; border: 2px solid #FFFFFF;
    }
    .timeline-date { font-size: 12px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .timeline-content { font-size: 14px; color: #1E293B; margin-top: 4px; font-weight: 500; }
    
    /* Meeting Card (MEJORADA) */
    .meeting-card {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 15px; margin-bottom: 10px;
        border-left: 4px solid #3B82F6; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .meeting-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .meeting-client { font-size: 14px; font-weight: 700; color: #1E293B; }
    .meeting-time { font-size: 12px; font-weight: 600; color: #3B82F6; background: #EFF6FF; padding: 4px 8px; border-radius: 4px; }
    .meeting-topic { font-size: 13px; color: #64748B; line-height: 1.4; }
    
    /* Next Best Action */
    .nba-box {
        background: linear-gradient(135deg, #F8FAFC 0%, #FFFFFF 100%);
        border: 1px solid #E2E8F0; border-radius: 8px; padding: 20px; margin-top: 20px;
        border-left: 4px solid #3B82F6;
    }
    .nba-title { color: #2563EB; font-size: 13px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }
    .nba-text { color: #1E293B; font-size: 16px; font-weight: 500; line-height: 1.5; }

    /* Buttons & Tags */
    .tag { background: #F1F5F9; color: #475569; padding: 3px 10px; border-radius: 12px; font-size: 11px; display: inline-block; margin-right: 5px; font-weight: 600;}
    .btn-contact {
        display: inline-block; background-color: #334155; color: white !important;
        padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; 
        text-decoration: none; text-align: center;
    }
    .btn-contact:hover { background-color: #0F172A; }
    
    div[data-testid="stDataFrame"] { border: 1px solid #E2E8F0; background: white; }
</style>
""", unsafe_allow_html=True)

# --- HELPER HTML CLEANER ---
def clean_html(html_str):
    return html_str.replace("\n", "").replace("    ", "")

def format_euro(val):
    return f"{val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

# --- LÓGICA DE NEGOCIO ---
def generate_next_best_action(row):
    tier = str(row['Tier'])
    gap = row.get('Gap_Potencial', 0)
    risk = row.get('Return_Risk_Prob', 0)
    
    if risk > 0.4: return "Atención: Llamada de cortesía para asegurar satisfacción (Riesgo Alto)."
    elif "VIC" in tier: return "Concierge: Agendar cita privada para ver colección 'Hermès' recién llegada."
    elif "Gold" in tier: return "Venta: Ofrecer acceso anticipado a web (Pre-Upload 24h)."
    elif gap > 3000: return "Upselling: Enviar propuesta de inversión en clásicos."
    else: return "Fidelización: Email automatizado con selección de 'New Arrivals'."

def process_client_data_advanced(df):
    if df is None or df.empty: return pd.DataFrame()
    data = df.copy()
    
    # Limpieza
    data['City'] = data['City'].fillna('Desconocido')
    data['Tier'] = data['Tier'].fillna('Standard')
    data['Brand_Affinity'] = data['Brand_Affinity'].fillna('General')
    data['Name'] = data['Name'].fillna('Cliente Anónimo')
    data['Sociological_Profile'] = data['Sociological_Profile'].fillna('No Definido')
    
    # Simulación
    np.random.seed(42)
    data['Fashion_Wallet'] = pd.to_numeric(data['Fashion_Wallet'], errors='coerce').fillna(5000)
    
    if 'Total_Spend' not in data.columns:
        data['Total_Spend'] = data['Fashion_Wallet'] * np.random.uniform(0.1, 0.8, size=len(data))
    data['Total_Spend'] = pd.to_numeric(data['Total_Spend'], errors='coerce').fillna(0)
    
    data['Share_of_Wallet'] = (data['Total_Spend'] / data['Fashion_Wallet'].replace(0, 1)) * 100
    data['Gap_Potencial'] = data['Fashion_Wallet'] - data['Total_Spend']
    data['Next_Best_Action'] = data.apply(generate_next_best_action, axis=1)
    
    today = datetime.now()
    def get_simulated_extras(row):
        random_day = np.random.randint(1, 28)
        random_month = np.random.randint(1, 13)
        bday = datetime(today.year, random_month, random_day)
        is_bday_close = abs((bday - today).days) < 7
        
        brands = str(row['Brand_Affinity']).split('|')
        target_brand = brands[0] if brands else "Hermès"
        wishlist = f"{target_brand} {np.random.choice(['Kelly 28', 'Birkin 30', 'Flap Bag'])}"
        
        is_vendor = np.random.random() < 0.3 
        buy_back_total = (row['Total_Spend'] * np.random.uniform(0.2, 0.6)) if is_vendor else 0
        
        return pd.Series([bday, is_bday_close, wishlist, buy_back_total], index=['Birth_Date', 'Is_Bday_Close', 'Active_Wishlist', 'Buy_Back_Total'])

    extras = data.apply(get_simulated_extras, axis=1)
    data = pd.concat([data, extras], axis=1)
    return data

def get_wishlist_matches(wishlist_item, df_inv):
    if df_inv.empty or not wishlist_item: return pd.DataFrame()
    target = wishlist_item.split()[0]
    matches = df_inv[df_inv['Marca'].str.contains(target, case=False, na=False)].copy()
    if not matches.empty:
        return matches.sort_values('Precio_Venta_EUR', ascending=False).head(2)
    return pd.DataFrame()

# --- CARGA ---
try:
    db = load_data()
    df_clients = db.get('clients')
    df_inventory = db.get('inventory')
except Exception as e:
    st.error(f"Error sistema: {e}")
    st.stop()

if df_clients is None or df_clients.empty:
    st.error("Faltan datos de clientes.")
    st.stop()

df = process_client_data_advanced(df_clients)

if 'filters' not in st.session_state:
    st.session_state.filters = {'city': 'Todas', 'tier': 'Todas', 'brand': 'Todas', 'profile': 'Todos'}

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### HERAS PURSE AI")
    st.caption("Client 360 Suite")
    
    cities = ["Todas"] + sorted(list(df['City'].unique()))
    st.session_state.filters['city'] = st.selectbox("Ciudad", cities, index=cities.index(st.session_state.filters['city']) if st.session_state.filters['city'] in cities else 0)
    
    tiers = ["Todas"] + sorted(list(df['Tier'].unique()))
    st.session_state.filters['tier'] = st.selectbox("Nivel", tiers, index=tiers.index(st.session_state.filters['tier']) if st.session_state.filters['tier'] in tiers else 0)
    
    profiles = ["Todos"] + sorted(list(df['Sociological_Profile'].unique()))
    st.session_state.filters['profile'] = st.selectbox("Perfil", profiles, index=profiles.index(st.session_state.filters['profile']) if st.session_state.filters['profile'] in profiles else 0)
    
    all_brands = set()
    for brands in df['Brand_Affinity'].unique():
        for b in str(brands).split('|'): all_brands.add(b.strip())
    brands_list = ["Todas"] + sorted(list(all_brands))
    st.session_state.filters['brand'] = st.selectbox("Afinidad", brands_list, index=brands_list.index(st.session_state.filters['brand']) if st.session_state.filters['brand'] in brands_list else 0)

# --- VIEW ---
df_view = df.copy()
if st.session_state.filters['city'] != "Todas": df_view = df_view[df_view['City'] == st.session_state.filters['city']]
if st.session_state.filters['tier'] != "Todas": df_view = df_view[df_view['Tier'] == st.session_state.filters['tier']]
if st.session_state.filters['profile'] != "Todos": df_view = df_view[df_view['Sociological_Profile'] == st.session_state.filters['profile']]
if st.session_state.filters['brand'] != "Todas": df_view = df_view[df_view['Brand_Affinity'].str.contains(st.session_state.filters['brand'], na=False, regex=False)]

st.title("Client 360 & CRM")

if df_view.empty:
    st.warning("⚠️ No se encontraron clientes.")
    st.stop()

# 1. KPIS CON TOOLTIPS
k1, k2, k3, k4 = st.columns(4)

with k1: 
    st.markdown(clean_html(f"""
    <div class="kpi-container">
        <div class="kpi-label">Cartera <div class="tooltip">ⓘ<span class="tooltiptext">Número total de clientes que coinciden con los filtros aplicados.</span></div></div>
        <div class="kpi-value">{len(df_view)}</div>
    </div>"""), unsafe_allow_html=True)

with k2: 
    st.markdown(clean_html(f"""
    <div class="kpi-container">
        <div class="kpi-label">Share of Wallet <div class="tooltip">ⓘ<span class="tooltiptext">Porcentaje del presupuesto anual de lujo del cliente que gasta CON NOSOTROS vs. la competencia.</span></div></div>
        <div class="kpi-value" style="color:#16A34A">{df_view['Share_of_Wallet'].mean():.1f}%</div>
    </div>"""), unsafe_allow_html=True)

with k3: 
    st.markdown(clean_html(f"""
    <div class="kpi-container">
        <div class="kpi-label">Latente <div class="tooltip">ⓘ<span class="tooltiptext">Oportunidad de venta restante: (Presupuesto Total Estimado - Gasto Actual). Dinero que aún podemos capturar.</span></div></div>
        <div class="kpi-value" style="color:#2563EB">{format_euro(df_view['Gap_Potencial'].sum())}</div>
    </div>"""), unsafe_allow_html=True)

with k4: 
    vic_c = len(df_view[df_view['Tier'].astype(str).str.contains("VIC", na=False)])
    st.markdown(clean_html(f"""
    <div class="kpi-container">
        <div class="kpi-label">VICs <div class="tooltip">ⓘ<span class="tooltiptext">Clientes 'Very Important Client' (Top 1% de facturación). Requieren atención Concierge.</span></div></div>
        <div class="kpi-value">{vic_c}</div>
    </div>"""), unsafe_allow_html=True)

# 2. CHARTS
st.markdown('<div class="section-title">Mapa de Valor</div>', unsafe_allow_html=True)
c1, c2 = st.columns([2, 1])
with c1:
    fig = px.scatter(df_view, x="Age", y="Fashion_Wallet", color="Tier", size="Total_Spend", hover_name="Name",
                     color_discrete_map={"VIC (Top 1%)": "#0F172A", "Gold (Recurrente)": "#D4AF37", "Standard (Ocasional)": "#94A3B8"})
    fig.update_layout(template="plotly_white", height=300, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig, use_container_width=True)
with c2:
    prof_counts = df_view['Sociological_Profile'].value_counts().reset_index()
    fig_p = px.pie(prof_counts, values='count', names='Sociological_Profile', hole=0.6, color_discrete_sequence=px.colors.qualitative.Prism)
    fig_p.update_layout(template="plotly_white", height=300, showlegend=False, margin=dict(l=20,r=20,t=20,b=20))
    fig_p.update_traces(textposition='inside', textinfo='label+percent')
    st.plotly_chart(fig_p, use_container_width=True)

# 3. LISTAS
st.markdown('<div class="section-title">Listas de Activación (CRM)</div>', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["Top VICs", "Upselling", "Riesgo / Atención"])

def render_client_list(dataframe, border_color, show_risk=False):
    if dataframe.empty:
        st.caption("Sin resultados.")
        return
    for _, r in dataframe.iterrows():
        brand = str(r['Brand_Affinity']).split('|')[0]
        risk_info = ""
        btn_color = border_color
        
        if show_risk:
            risk_info = f"<div style='font-size:13px; color:#DC2626; margin-top:6px; font-weight:500;'>⚠️ Prob. Devolución: {r.get('Return_Risk_Prob', 0):.0%} • Sensibilidad: {r.get('Price_Sensitivity', 'Media')}</div>"
            btn_color = "#DC2626"
            
        html = f"""
        <div class="client-card" style="border-left: 4px solid {border_color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div class="client-name">
                        {r['Name']} <span class="tag" style="background:#F1F5F9; color:#64748B;">{r['Tier']}</span>
                    </div>
                    <div class="client-meta">
                        {r['City']} • {r['Sociological_Profile']}
                    </div>
                    {risk_info}
                    <div style="margin-top:6px;">
                        <span class="tag" style="background:#F1F5F9;">{brand}</span>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:700; color:{border_color}; font-size:16px; margin-bottom:8px;">{format_euro(r['Total_Spend'])}</div>
                    <a href="mailto:{r['Email']}" class="btn-contact" style="background-color:{btn_color};">Contactar</a>
                </div>
            </div>
        </div>
        """
        st.markdown(clean_html(html), unsafe_allow_html=True)

with tab1: render_client_list(df_view[df_view['Tier'].astype(str).str.contains("VIC", na=False)].sort_values('Total_Spend', ascending=False).head(5), "#0F172A")
with tab2: render_client_list(df_view.sort_values('Gap_Potencial', ascending=False).head(5), "#475569")
with tab3: render_client_list(df_view.sort_values('Return_Risk_Prob', ascending=False).head(5), "#991B1B", show_risk=True)

# 4. DETALLE
st.markdown('<div class="section-title">Expediente de Cliente 360°</div>', unsafe_allow_html=True)
all_clients_global = sorted(df['Name'].dropna().unique())
sel_client_name = st.selectbox("Buscar Cliente Global", all_clients_global, index=None, placeholder="Escribe para buscar...")

if sel_client_name:
    c = df[df['Name'] == sel_client_name].iloc[0]
    
    bday_alert = ""
    if c['Is_Bday_Close']:
        bday_alert = f"""<div style="background:#FEF2F2; color:#991B1B; padding:12px; border-radius:6px; margin-bottom:20px; font-weight:600; display:flex; align-items:center; gap:10px;">Atención! Su cumpleaños es el {c['Birth_Date'].strftime('%d-%b')}.</div>"""

    # FICHA PRINCIPAL
    html_header = f"""
    {bday_alert}
    <div style="background:white; padding:25px; border:1px solid #E2E8F0; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <h2 style="margin:0; color:#1E293B; font-size:24px;">{c['Name']}</h2>
                <p style="color:#64748B; margin:8px 0 15px 0; font-size:15px;">{c['City']} • {c['Age']} años • {c['Email']}</p>
                <div style="display:flex; gap:10px;">
                    <span style="background:#F1F5F9; color:#334155; padding:6px 12px; border-radius:20px; font-weight:600; font-size:12px;">{c['Tier']}</span>
                    <span style="background:#EFF6FF; color:#1D4ED8; padding:6px 12px; border-radius:20px; font-weight:600; font-size:12px;">{c['Sociological_Profile']}</span>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:13px; color:#64748B; text-transform:uppercase; font-weight:600; display:flex; justify-content:flex-end; align-items:center;">
                    LTV Total <div class="tooltip">ⓘ<span class="tooltiptext">Lifetime Value: Suma total de compras históricas del cliente.</span></div>
                </div>
                <div style="font-size:24px; color:#0F172A; font-weight:700;">{format_euro(c['Total_Spend'])}</div>
            </div>
        </div>
        <div class="nba-box">
            <div class="nba-title">Siguiente Mejor Acción (IA)</div>
            <div class="nba-text">{c['Next_Best_Action']}</div>
        </div>
    </div>
    """
    st.markdown(clean_html(html_header), unsafe_allow_html=True)

    st.write("")
    
    # --- PESTAÑAS (Con pestaña Reuniones) ---
    tab_wish, tab_back, tab_journey, tab_meet = st.tabs(["Radar de Deseos", "Historial & Buy-Back", "Customer Journey", "Reuniones"])
    
    with tab_wish:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"**Busca Activamente:**")
            st.info(f" {c['Active_Wishlist']}")
            st.caption("Información basada en afinidad.")
        with c2:
            st.markdown("**Coincidencias en Stock:**")
            matches = get_wishlist_matches(c['Active_Wishlist'], df_inventory)
            if not matches.empty:
                for _, m in matches.iterrows():
                    match_html = f"""
                    <div class="wish-match">
                        <div class="wish-title">¡Encontrado! {m['Marca']} {m['Modelo']}</div>
                        <div style="font-size:14px; margin-top:5px; color:#14532D; font-weight:600;">Precio: {format_euro(m['Precio_Venta_EUR'])}</div>
                    </div>
                    """
                    st.markdown(clean_html(match_html), unsafe_allow_html=True)
            else:
                st.write("❌ No hay coincidencias exactas.")

    with tab_back:
        c1, c2 = st.columns(2)
        with c1:
            if c['Buy_Back_Total'] > 0:
                st.markdown(clean_html("""<div style="display:flex; align-items:center;"><strong>Resumen de Proveedor</strong> <div class="tooltip">ⓘ<span class="tooltiptext">Dinero que hemos pagado al cliente por sus bolsos (Nosotros compramos).</span></div></div>"""), unsafe_allow_html=True)
                st.metric("Pagado al Cliente", format_euro(c['Buy_Back_Total']))
                st.caption(f"Valor total de mercancía adquirida a este cliente.")
            else:
                st.info("Este cliente aún no nos ha vendido nada.")
        with c2:
            st.markdown("**Diario de Relación**")
            timeline_html = """
            <div class="timeline-container">
                <div class="timeline-item">
                    <div class="timeline-date">15 Ene 2024</div>
                    <div class="timeline-content">Llamada de seguimiento. Interesada en Kelly 28.</div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-date">02 Dic 2023</div>
                    <div class="timeline-content">Visita privada a showroom.</div>
                </div>
            </div>
            """
            st.markdown(clean_html(timeline_html), unsafe_allow_html=True)

    with tab_journey:
        dates = pd.date_range(end=datetime.now(), periods=6, freq='3ME')
        vals = np.random.randint(500, 3000, size=6)
        df_j = pd.DataFrame({'Fecha': dates, 'Compra': vals})
        fig = px.line(df_j, x='Fecha', y='Compra', markers=True)
        fig.update_layout(template="plotly_white", height=250, margin=dict(l=20,r=20,t=30,b=20))
        st.plotly_chart(fig, use_container_width=True)

    # --- PESTAÑA REUNIONES MEJORADA ---
    with tab_meet:
        # Filtrar reuniones del cliente seleccionado
        my_meetings = [m for m in st.session_state.meetings if m['client_name'] == c['Name']]
        
        if my_meetings:
            for meet in my_meetings:
                meet_html = f"""
                <div class="meeting-card">
                    <div class="meeting-header">
                        <div class="meeting-client">{meet['client_name']}</div>
                        <div class="meeting-time">{meet['date']} | {meet['time']}</div>
                    </div>
                    <div class="meeting-topic">{meet['topic']}</div>
                </div>
                """
                st.markdown(clean_html(meet_html), unsafe_allow_html=True)
        else:
            st.info("No hay reuniones programadas para este cliente.")

    # --- ZONA DE AGENDA Y CONTACTO ---
    st.markdown("### Agenda & Contacto")
    col1, col2 = st.columns([1, 2])
    with col1:
        date_meet = st.date_input("Fecha", datetime.today() + timedelta(days=1))
        time_meet = st.time_input("Hora", time(10, 0)) 
        
        # Tema predeterminado basado en NBA
        default_topic = c['Next_Best_Action'] if c['Next_Best_Action'] else "Reunión de seguimiento"
        meet_topic = st.text_input("Tema de la Reunión", value=default_topic)
        
        if st.button("Agendar Reunión", use_container_width=True):
            new_meeting = {
                "client_name": c['Name'],
                "date": date_meet.strftime('%d-%b-%Y'),
                "time": time_meet.strftime('%H:%M'),
                "topic": meet_topic  # Usamos el tema personalizado
            }
            st.session_state.meetings.append(new_meeting)
            st.success(f"Cita guardada en la ficha de {c['Name']}.")
            st.rerun()
            
    with col2:
        st.write("") 
        st.write("")
        c_a, c_b = st.columns(2)
        
        phone = "34600000000" 
        msg_text = f"Hola {c['Name'].split()[0]}, soy tu asesor de Heras Purse."
        wa_url = f"https://wa.me/{phone}?text={msg_text}"
        
        with c_a: st.markdown(clean_html(f'<a href="mailto:{c["Email"]}" class="btn-contact" style="display:block;">Email</a>'), unsafe_allow_html=True)
        with c_b: st.markdown(clean_html(f'<a href="{wa_url}" target="_blank" class="btn-contact" style="display:block; background-color:#16A34A;">WhatsApp</a>'), unsafe_allow_html=True)