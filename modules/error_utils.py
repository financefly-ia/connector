# modules/error_utils.py
import logging
import streamlit as st

logger = logging.getLogger(__name__)

# =========================================================
# ERROR HANDLING UTILITIES
# =========================================================
def log_and_display_error(error_message, technical_details=None, show_support_info=True):
    """
    Logs technical error details and displays user-friendly error message.
    
    Args:
        error_message (str): User-friendly error message to display
        technical_details (str, optional): Technical details to log
        show_support_info (bool): Whether to show support contact information
    """
    if technical_details:
        logger.error(f"Error: {technical_details}", exc_info=True)
    
    st.error(f"❌ {error_message}")
    
    if show_support_info:
        st.info("💡 Se o problema persistir, entre em contato com o suporte técnico.")

def display_environment_errors(errors):
    """
    Displays environment configuration errors in a user-friendly format.
    
    Args:
        errors (list): List of error messages from environment validation
    """
    logger.error(f"Environment validation failed with {len(errors)} errors")
    st.error("❌ **Configuração incompleta**")
    st.write("As seguintes variáveis de ambiente precisam ser configuradas:")
    for error in errors:
        st.write(f"• {error}")
    st.write("")
    st.info("💡 **Como corrigir:**")
    st.write("1. Verifique se o arquivo `.env` existe na raiz do projeto")
    st.write("2. Certifique-se de que as variáveis estão definidas corretamente:")
    st.code("""PLUGGY_CLIENT_ID=seu_client_id_aqui
PLUGGY_CLIENT_SECRET=seu_client_secret_aqui""")
    st.write("3. Reinicie a aplicação após fazer as alterações")
    st.stop()

def handle_pluggy_error(error, user_email=None):
    """
    Handles Pluggy-related errors with appropriate logging and user messaging.
    
    Args:
        error (Exception): The error that occurred
        user_email (str, optional): User email for logging context
    """
    if isinstance(error, ValueError):
        # User-friendly error messages from pluggy_utils
        logger.warning(f"User-facing error for {user_email or 'unknown'}: {error}")
        st.error(f"❌ {str(error)}")
        st.info("💡 Tente novamente em alguns instantes. Se o problema persistir, entre em contato com o suporte.")
    else:
        # Log the actual error for debugging but show user-friendly message
        logger.error(f"Unexpected error for {user_email or 'unknown'}: {error}", exc_info=True)
        st.error("❌ Erro inesperado ao gerar token de conexão. Tente novamente.")
        st.info("💡 Se o problema persistir, entre em contato com o suporte técnico.")