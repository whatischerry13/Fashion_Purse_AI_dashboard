import streamlit as st
from src.rag.engine import LuxuryAssistant
import gc
import traceback

# --- 1. MOTOR DE IA (CON DIAGNÓSTICO VISIBLE) ---
@st.cache_resource(show_spinner=False)
def get_engine_instance():
    """
    Intenta cargar el cerebro. Si falla, MUESTRA EL ERROR EXACTO.
    """
    try:
        gc.collect()
        return LuxuryAssistant()
    except Exception as e:
        # AQUÍ ESTÁ EL CAMBIO: Guardamos el error para mostrarlo
        error_trace = traceback.format_exc()
        st.session_state.startup_error = f"{str(e)} \n\n {error_trace}"
        print(f"❌ Error Crítico iniciando Aura: {e}")
        return None

def force_reset_aura():
    """Borra caché y fuerza reinicio."""
    st.cache_resource.clear()
    for key in ["aura_bot", "aura_history", "startup_error"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# --- 2. RENDERIZADO ---
def render_aura(context=""):
    
    # CSS
    st.markdown("""
    <style>
        div[data-testid="stPopover"] { position: fixed; bottom: 30px; right: 30px; z-index: 99999; }
        div[data-testid="stPopover"] > button {
            width: 60px; height: 60px; border-radius: 50%;
            background-color: #0F172A; color: white; border: 1px solid #334155;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3); font-size: 24px;
        }
        .aura-error-msg { background: #FEE2E2; color: #991B1B; padding: 10px; border: 1px solid #F87171; border-radius: 8px; font-size: 0.8rem;}
    </style>
    """, unsafe_allow_html=True)

    # Inicializar Historial
    if "aura_history" not in st.session_state:
        st.session_state.aura_history = [{"role": "assistant", "content": "Hola. Soy Aura."}]

    # Intentar conectar
    if "aura_bot" not in st.session_state or st.session_state.aura_bot is None:
        engine = get_engine_instance()
        if engine and hasattr(engine, 'chain'):
            st.session_state.aura_bot = engine
        else:
            st.session_state.aura_bot = None

    # UI BURBUJA
    with st.popover("Heras Purse AI chatbot", use_container_width=False):
        c1, c2 = st.columns([3, 1])
        with c1: st.markdown("### Aura AI")
        with c2: 
            if st.button("♻️"): force_reset_aura()

        # SI HAY ERROR DE ARRANQUE, LO MOSTRAMOS AQUÍ EN ROJO
        if "startup_error" in st.session_state:
            st.error("🚨 ERROR DE ARRANQUE DETECTADO:")
            st.code(st.session_state.startup_error, language="bash")
        
        # Chat Normal
        chat_container = st.container(height=300)
        with chat_container:
            for msg in st.session_state.aura_history:
                role_icon = "✨" if msg["role"] == "assistant" else "👤"
                st.markdown(f"**{role_icon}**: {msg['content']}")

        if prompt := st.chat_input("Escribe..."):
            st.session_state.aura_history.append({"role": "user", "content": prompt})
            
            if st.session_state.aura_bot:
                try:
                    response = st.session_state.aura_bot.ask(f"[Ctx: {context}] {prompt}")
                    st.session_state.aura_history.append({"role": "assistant", "content": response["answer"]})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error respondiendo: {e}")
            else:
                st.error("⚠️ Aura no pudo arrancar. Mira el error arriba.")