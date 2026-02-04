import streamlit as st
from src.rag.engine import LuxuryAssistant
import gc

# --- 1. OPTIMIZACIÓN DE MEMORIA (EL TRUCO) ---
@st.cache_resource(show_spinner=False, ttl=3600)
def get_shared_engine():
    """
    Patrón Singleton: Carga el modelo pesado UNA sola vez en el servidor
    y lo reutiliza para siempre. Esto evita que la RAM explote.
    """
    try:
        # Forzamos limpieza antes de cargar
        gc.collect()
        return LuxuryAssistant()
    except Exception as e:
        print(f"Error cargando motor IA: {e}")
        return None

# --- 2. LÓGICA DE GESTIÓN ---
def init_aura():
    """Conecta la sesión actual al motor compartido."""
    try:
        # En vez de crear uno nuevo (LuxuryAssistant()), pedimos el compartido
        engine = get_shared_engine()
        
        if engine and hasattr(engine, 'chain') and engine.chain is not None:
            st.session_state.aura_bot = engine
            return True
        return False
    except Exception:
        return False

def render_aura(context=""):
    """
    Renderiza el botón flotante (Burbuja).
    """
    # 1. ESTILOS CSS
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
    </style>
    """, unsafe_allow_html=True)

    # 2. GESTIÓN DE ESTADO
    if "aura_history" not in st.session_state:
        st.session_state.aura_history = [{"role": "assistant", "content": "Hola. Soy Aura. ¿En qué puedo ayudarte con estos datos?"}]

    # Si no tenemos el bot conectado en esta sesión, lo conectamos al motor caché
    if "aura_bot" not in st.session_state:
        init_aura()

    # 3. BURBUJA FLOTANTE
    with st.popover("Aura AI", use_container_width=False):
        st.markdown("### Aura AI")
        st.caption("Asistente Virtual")
        
        chat_container = st.container(height=400)
        with chat_container:
            for msg in st.session_state.aura_history:
                div_class = "aura-user-msg" if msg["role"] == "user" else "aura-bot-msg"
                st.markdown(f"<div class='{div_class}'>{msg['content']}</div>", unsafe_allow_html=True)

        if prompt := st.chat_input("Pregunta a Aura..."):
            st.session_state.aura_history.append({"role": "user", "content": prompt})
            
            # Verificación defensiva
            if "aura_bot" in st.session_state and st.session_state.aura_bot:
                try:
                    full_prompt = f"[Contexto: {context}] {prompt}"
                    response = st.session_state.aura_bot.ask(full_prompt)
                    st.session_state.aura_history.append({"role": "assistant", "content": response['answer']})
                    
                    # Limpieza agresiva de memoria tras generar respuesta
                    gc.collect()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Conectando con Aura...")
                init_aura()
                st.rerun()