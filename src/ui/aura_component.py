import streamlit as st
from src.rag.engine import LuxuryAssistant
import gc

# --- 1. MOTOR DE IA (CACHÉ INTELIGENTE) ---
@st.cache_resource(show_spinner=False)
def get_engine_instance():
    """
    Carga el modelo UNA sola vez y lo comparte.
    Si falla, devuelve None para que podamos manejarlo.
    """
    try:
        gc.collect() # Limpieza de memoria preventiva
        return LuxuryAssistant()
    except Exception as e:
        return None

def force_reset_aura():
    """Borra la caché y fuerza un reinicio limpio."""
    st.cache_resource.clear()
    if "aura_bot" in st.session_state:
        del st.session_state["aura_bot"]
    if "aura_history" in st.session_state:
        st.session_state.aura_history = []
    st.rerun()

# --- 2. RENDERIZADO DEL CHAT ---
def render_aura(context=""):
    """
    Renderiza la burbuja flotante con gestión de errores visible.
    """
    
    # CSS: Burbuja Flotante + Botón de Reinicio
    st.markdown("""
    <style>
        div[data-testid="stPopover"] { position: fixed; bottom: 30px; right: 30px; z-index: 99999; }
        div[data-testid="stPopover"] > button {
            width: 60px; height: 60px; border-radius: 50%;
            background-color: #0F172A; color: white; border: 1px solid #334155;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3); font-size: 24px; transition: transform 0.2s;
        }
        div[data-testid="stPopover"] > button:hover { transform: scale(1.1); background-color: #000000; }
        
        .aura-user-msg { background: #F1F5F9; color: #1E293B; padding: 10px; border-radius: 12px 12px 2px 12px; margin-bottom: 8px; text-align: right; margin-left: 20px; font-size: 0.9rem;}
        .aura-bot-msg { background: #FFFFFF; color: #0F172A; padding: 10px; border: 1px solid #E2E8F0; border-radius: 12px 12px 12px 2px; margin-bottom: 8px; font-size: 0.9rem;}
        .aura-error-msg { background: #FEE2E2; color: #991B1B; padding: 10px; border: 1px solid #F87171; border-radius: 8px; margin-bottom: 8px; font-size: 0.85rem;}
    </style>
    """, unsafe_allow_html=True)

    # Inicializar Historial
    if "aura_history" not in st.session_state:
        st.session_state.aura_history = [{"role": "assistant", "content": "Hola. Soy Aura. ¿En qué puedo ayudarte?"}]

    # --- LÓGICA DE CONEXIÓN ---
    if "aura_bot" not in st.session_state or st.session_state.aura_bot is None:
        engine = get_engine_instance()
        if engine and hasattr(engine, 'chain') and engine.chain:
            st.session_state.aura_bot = engine
        else:
            # Si falla la carga, no bloqueamos, pero avisamos dentro del chat
            st.session_state.aura_bot = None

    # --- UI DE LA BURBUJA ---
    with st.popover("💬", use_container_width=False):
        # Cabecera con Botón de Reinicio
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown("### Aura AI")
            st.caption("Asistente Virtual")
        with c2:
            if st.button("♻️", help="Reiniciar Aura"):
                force_reset_aura()

        # Contenedor de Chat
        chat_container = st.container(height=350)
        with chat_container:
            for msg in st.session_state.aura_history:
                if msg["role"] == "user":
                    st.markdown(f"<div class='aura-user-msg'>{msg['content']}</div>", unsafe_allow_html=True)
                elif msg["role"] == "error":
                    st.markdown(f"<div class='aura-error-msg'>⚠️ {msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='aura-bot-msg'>{msg['content']}</div>", unsafe_allow_html=True)

        # Input de Usuario
        if prompt := st.chat_input("Escribe aquí...", key="aura_float_input"):
            # 1. Pintar usuario
            st.session_state.aura_history.append({"role": "user", "content": prompt})
            
            # 2. Generar respuesta
            if st.session_state.aura_bot:
                try:
                    with st.spinner("Aura está pensando..."):
                        # Contexto + Prompt
                        full_prompt = f"[Contexto Pantalla: {context}] {prompt}"
                        
                        # LLAMADA AL CEREBRO (Esta es la línea crítica)
                        response = st.session_state.aura_bot.ask(full_prompt)
                        
                        # Extraer respuesta
                        if isinstance(response, dict) and "answer" in response:
                            answer = response["answer"]
                        else:
                            answer = str(response)

                        st.session_state.aura_history.append({"role": "assistant", "content": answer})
                        st.rerun()
                        
                except Exception as e:
                    # SI FALLA, LO MOSTRAMOS EN ROJO
                    error_msg = f"Error técnico: {str(e)}"
                    st.session_state.aura_history.append({"role": "error", "content": error_msg})
                    st.rerun()
            else:
                st.session_state.aura_history.append({"role": "error", "content": "Aura desconectada. Pulsa ♻️ arriba."})
                st.rerun()