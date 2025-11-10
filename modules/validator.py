# modules/validator.py
import os
import streamlit as st


def validate_env_var(key, required=True):
    """Verifica se a env está presente e loga no console."""
    value = os.getenv(key)

    if value:
        print(f"[VALIDATOR] {key} = OK")
        return value

    print(f"[VALIDATOR] ERRO: {key} não encontrada!")

    if required:
        st.warning(f"Variável de ambiente **{key}** não está configurada.")
    return None


def startup_validation():
    print("=== STARTUP VALIDATION INICIADA ===")

    # ------------------------------
    # ✅ 1. Valida Pluggy
    # ------------------------------
    print("[VALIDATOR] Checando Pluggy CLIENT ID / SECRET...")
    pluggy_id = validate_env_var("PLUGGY_CLIENT_ID")
    pluggy_secret = validate_env_var("PLUGGY_CLIENT_SECRET")

    if not pluggy_id or not pluggy_secret:
        st.error("Configuração do Pluggy incompleta. Verifique CLIENT_ID / CLIENT_SECRET.")
        return  # não derruba a aplicação

    # ------------------------------
    # ✅ 2. Valida DB
    # ------------------------------
    print("[VALIDATOR] Checando variáveis do PostgreSQL...")
    db_host = validate_env_var("DB_HOST")
    db_port = validate_env_var("DB_PORT")
    db_user = validate_env_var("DB_USER")
    db_pass = validate_env_var("DB_PASSWORD")
    db_name = validate_env_var("DB_NAME")
    db_ssl = validate_env_var("DB_SSLMODE", required=False)

    # Se qualquer variável crítica estiver vazia → apenas alerta, sem crash
    if not all([db_host, db_port, db_user, db_pass, db_name]):
        st.warning(
            "Algumas variáveis do banco não estão configuradas.\n"
            "O conector pode não conseguir salvar os dados."
        )

    # ------------------------------
    # ✅ 3. Log final
    # ------------------------------
    print("=== STARTUP VALIDATION FINALIZADA ===")
