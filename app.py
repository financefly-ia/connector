import os
import streamlit as st
from modules.validator import startup_validation
from modules.pluggy import create_connect_token
from modules.db import save_client

# =========================================================
# CONFIG STREAMLIT
# =========================================================
st.set_page_config(
    page_title="Financefly Connector",
    page_icon="💸",
    layout="centered"
)

# =========================================================
# STARTUP SAFE
# =========================================================
with st.spinner("Inicializando ambiente..."):
    try:
        startup_validation()
    except Exception as e:
        st.warning(f"Aviso durante inicialização: {e}")

# =========================================================
# SESSION STATE
# =========================================================
if "connect_token" not in st.session_state:
    st.session_state.connect_token = None

if "form_data" not in st.session_state:
    st.session_state.form_data = {"name": "", "email": ""}

if "item_processed" not in st.session_state:
    st.session_state.item_processed = False


# =========================================================
# VERIFICAÇÃO URL (itemId)
# =========================================================
params = st.query_params
item_id = params.get("itemId") if params else None

# PROCESSA itemId só uma vez e sem loop
if item_id and not st.session_state.item_processed:
    name = st.session_state.form_data.get("name", "")
    email = st.session_state.form_data.get("email", "")

    if name and email:
        try:
            save_client(name, email, item_id)
            st.success("Conta conectada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar no banco: {e}")
            print("🔥 ERRO save_client:", e)
    else:
        st.warning("itemId recebido, mas nome/email não foram preenchidos.")

    st.session_state.item_processed = True


# =========================================================
# UI / FORM
# =========================================================
st.title("Financefly Connector")
st.caption("Conecte sua conta bancária via Pluggy com segurança.")

with st.form("client_form"):
    name = st.text_input("Nome completo", st.session_state.form_data["name"])
    email = st.text_input("E-mail", st.session_state.form_data["email"])
    submit = st.form_submit_button("Conectar conta")

if submit:
    if not name or not email:
        st.warning("Preencha todos os campos.")
    else:
        st.session_state.form_data = {"name": name, "email": email}
        try:
            token = create_connect_token(client_user_id=email)
            st.session_state.connect_token = token
        except Exception as e:
            st.error(f"Erro ao gerar token: {e}")
            print("🔥 ERRO create_connect_token:", e)


# =========================================================
# WIDGET PLUGGY
# =========================================================
if st.session_state.connect_token:
    st.info("Abrindo o Pluggy Connect…")

    html = f"""
    <script src="https://cdn.pluggy.ai/pluggy-connect/v2.9.2/pluggy-connect.js"></script>
    <script>
        const connect = new PluggyConnect({{
            connectToken: "{st.session_state.connect_token}",
            includeSandbox: false,
            language: "pt",
            theme: "dark",
        }});
        connect.open();
    </script>
    """

    st.components.v1.html(html, height=600)
