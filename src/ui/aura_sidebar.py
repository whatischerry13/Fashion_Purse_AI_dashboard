import streamlit as st
import sys
from pathlib import Path

# --- 1. CONFIGURACIÓN DE RUTAS ---
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path: sys.path.append(str(project_root))

# Importamos el Engine actualizado
try:
    from src.rag.engine import LuxuryAssistant
except ImportError:
    # Fallback por si hay problemas de importación durante el desarrollo
    LuxuryAssistant = None

def init_aura_state():
    """Inicializa el historial y el bot en la sesión."""
    # 1. Historial de Chat
    if "aura_history" not in st.session_state:
        st.session_state.aura_history = [
            {"role": "assistant", "content": "Bienvenida. Soy Aura. ¿Buscas alguna pieza especial hoy?"}
        ]
    
    # 2. Inicializar el Bot (Objeto completo)
    # Nota: Guardamos 'aura_bot', no 'aura_chain', para tener acceso al método .ask()
    if "aura_bot" not in st.session_state and LuxuryAssistant is not None:
        try:
            with st.spinner(""): # Spinner invisible
                st.session_state.aura_bot = LuxuryAssistant()
        except Exception as e:
            st.session_state.aura_error = str(e)

def render_aura_widget():
    """
    Renderiza el botón flotante (Burbuja) en la esquina inferior derecha.
    Usa CSS para el estilo y st.popover para la funcionalidad.
    """
    
    # --- CSS: ESTILO FLOTANTE ---
    st.markdown("""
    <style>
        /* Posicionar el botón flotante abajo a la derecha */
        div[data-testid="stPopover"] {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 99999; /* Siempre encima */
        }

        /* Estilizar el botón para que sea un círculo perfecto */
        div[data-testid="stPopover"] > button {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background-color: #111827; /* Negro Lujo */
            color: white;
            border: 2px solid #374151;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            font-size: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }

        /* Efecto Hover */
        div[data-testid="stPopover"] > button:hover {
            transform: scale(1.1);
            background-color: #000000;
            border-color: #FFFFFF;
        }
        
        /* Estilos de los mensajes del chat */
        .aura-user-msg { 
            background: #F3F4F6; color: #1F2937; padding: 10px 14px; 
            border-radius: 12px 12px 2px 12px; margin-bottom: 8px; font-size: 0.9rem; 
            text-align: right; margin-left: 20px;
        }
        .aura-bot-msg { 
            background: #FFFFFF; color: #111827; padding: 10px 14px; 
            border: 1px solid #E5E7EB; border-radius: 12px 12px 12px 2px; 
            margin-bottom: 8px; font-size: 0.9rem; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

    # Inicializar estado
    init_aura_state()

    # --- WIDGET FLOTANTE (POPOVER) ---
    # Usamos un emoji "💬" para el icono de la burbuja
    with st.popover("💬", use_container_width=False):
        st.markdown("### Aura AI")
        st.caption("Private Concierge & Strategy")
        
        # Contenedor con altura fija para scroll
        chat_container = st.container(height=400)
        
        with chat_container:
            for msg in st.session_state.aura_history:
                div_class = "aura-user-msg" if msg["role"] == "user" else "aura-bot-msg"
                st.markdown(f"<div class='{div_class}'>{msg['content']}</div>", unsafe_allow_html=True)

        # Input de Usuario
        if prompt := st.chat_input("Pregunta por stock, precios...", key="aura_float_input"):
            
            # A. Guardar mensaje de usuario
            st.session_state.aura_history.append({"role": "user", "content": prompt})
            
            # B. Generar Respuesta
            try:
                if "aura_bot" in st.session_state:
                    # --- AQUÍ ESTÁ EL CAMBIO IMPORTANTE ---
                    # Llamamos al método .ask() que maneja internamente el error 429
                    response = st.session_state.aura_bot.ask(prompt)
                    answer = response['answer']
                    
                    # C. Guardar mensaje del bot
                    st.session_state.aura_history.append({
                        "role": "assistant", 
                        "content": answer
                    })
                    st.rerun() # Refrescar para mostrar el mensaje
                else:
                    # Si el bot no cargó (ej: error de API Key), mostramos aviso
                    st.error("⚠️ Aura no está conectada. Revisa la configuración.")
            except Exception as e:
                # Error de último recurso
                st.error(f"Error inesperado: {e}")