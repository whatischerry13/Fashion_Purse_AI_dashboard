import streamlit as st
from src.rag.engine import LuxuryAssistant

# --- LÓGICA DE GESTIÓN (CEREBRO) ---
def init_aura():
    """Inicializa o revive a Aura si está corrupta (Anti-Zombi)."""
    try:
        # Intentamos crear una nueva instancia
        new_aura = LuxuryAssistant()
        
        # Verificamos que tenga cerebro (chain)
        if hasattr(new_aura, 'chain') and new_aura.chain is not None:
            st.session_state.aura_bot = new_aura
            return True
        return False
    except Exception:
        return False

def render_aura(context=""):
    """
    Renderiza el botón flotante (Burbuja) en la esquina inferior derecha.
    Args:
        context (str): Información oculta sobre qué está viendo el usuario (ej: 'Viendo Ventas').
    """
    
    # 1. ESTILOS CSS (TU DISEÑO DE LUJO + AJUSTES)
    st.markdown("""
    <style>
        /* Botón flotante */
        div[data-testid="stPopover"] {
            position: fixed; bottom: 30px; right: 30px; z-index: 99999;
        }
        /* Estilo del botón circular */
        div[data-testid="stPopover"] > button {
            width: 60px; height: 60px; border-radius: 50%;
            background-color: #0F172A; color: white; border: 1px solid #334155;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-size: 24px; transition: transform 0.2s;
        }
        div[data-testid="stPopover"] > button:hover {
            transform: scale(1.1); background-color: #000000; border-color: #FFFFFF;
        }
        /* Burbujas del chat */
        .aura-user-msg { 
            background: #F1F5F9; color: #1E293B; padding: 10px 14px; 
            border-radius: 12px 12px 2px 12px; margin-bottom: 8px; font-size: 0.9rem; 
            text-align: right; margin-left: 20px;
        }
        .aura-bot-msg { 
            background: #FFFFFF; color: #0F172A; padding: 10px 14px; 
            border: 1px solid #E2E8F0; border-radius: 12px 12px 12px 2px; 
            margin-bottom: 8px; font-size: 0.9rem; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

    # 2. INICIALIZACIÓN DE ESTADO
    if "aura_history" not in st.session_state:
        st.session_state.aura_history = [
            {"role": "assistant", "content": "Bienvenida a Heras. Soy Aura. ¿En qué puedo ayudarte?"}
        ]

    # Chequeo Anti-Zombi: Si no hay bot o está roto, intentamos revivirlo
    if "aura_bot" not in st.session_state or not hasattr(st.session_state.aura_bot, 'chain'):
        # Intentamos revivir en silencio
        init_aura()

    # 3. WIDGET FLOTANTE (POPOVER)
    # El emoji 💬 será el icono del botón
    with st.popover("💬", use_container_width=False):
        st.markdown("### Aura AI")
        st.caption("Private Concierge & Strategy")
        
        # Contenedor con altura fija para scroll
        chat_container = st.container(height=400)
        
        # Pintar historial
        with chat_container:
            for msg in st.session_state.aura_history:
                div_class = "aura-user-msg" if msg["role"] == "user" else "aura-bot-msg"
                st.markdown(f"<div class='{div_class}'>{msg['content']}</div>", unsafe_allow_html=True)

        # Input de Usuario
        if prompt := st.chat_input("Pregunta a Aura...", key="aura_float_input"):
            
            # A. Guardar mensaje de usuario
            st.session_state.aura_history.append({"role": "user", "content": prompt})
            
            # B. Generar Respuesta
            if "aura_bot" in st.session_state and st.session_state.aura_bot:
                try:
                    # Inyectamos el contexto invisiblemente
                    full_prompt = f"[Contexto actual: {context}] {prompt}"
                    
                    response = st.session_state.aura_bot.ask(full_prompt)
                    answer = response['answer']
                    
                    st.session_state.aura_history.append({"role": "assistant", "content": answer})
                    st.rerun() # Refrescar para mostrar el mensaje nuevo
                except Exception:
                    st.error("Error de conexión con Aura.")
            else:
                # Si sigue muerta tras intentar revivirla
                st.error("⚠️ Aura se está reiniciando. Prueba en unos segundos.")
                init_aura() # Intentamos revivir para la próxima
                st.rerun()