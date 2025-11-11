import os
import streamlit as st
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from modules.validator import startup_validation
from modules.pluggy import create_connect_token
from modules.db import save_client
# (init_db desativado de propósito)


# =========================================================
# HEALTHCHECK SERVER (porta 8081)
# =========================================================
def start_healthcheck_server():
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            else:
                self.send_response(404)
                self.end_headers()

    server = HTTPServer(("0.0.0.0", 8081), HealthHandler)
    server.serve_forever()


threading.Thread(target=start_healthcheck_server, daemon=True).start()


# =========================================================
# STREAMLIT CONFIG
# =========================================================
st.set_page_config(
    page_title="Financefly Connector",
    page_icon="💸",    # icone novo
    layout="centered"
)


# =========================================================
# STARTUP SAFE
# =========================================================
with st.spinner("Inicializando ambiente..."):
    try:
        startup_validation()
        # init_db()  # mantido desativado
    except Exception as e:
        st.warning(f"Aviso durante inicialização: {e}")


# =========================================================
# SESSION STATE
# =========================================================
if "connect_token" not in st.session_state:
    st.session_state.connect_token = None

if "form_data" not in st.session_state:
    st.session_state.form_data = {"name": "", "email": ""}


# =========================================================
# HEADER
# =========================================================
st.title("Financefly Connector 💸")
st.caption("Conecte sua conta bancária via Pluggy com segurança e fluidez.")


# =========================================================
# PROCESSA ITEMID VIA QUERY PARAM
# =========================================================
params = st.query_params
item_id = params.get("itemId") if params else None

if item_id:
    name = st.session_state.form_data["name"]
    email = st.session_state.form_data["email"]

    if name and email:
        try:
            save_client(name, email, item_id)
            st.success("✅ Conta conectada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar no banco.")
            print("🔥 ERRO save_client:", e)
    else:
        st.warning("Recebemos o itemId, mas faltam nome e email.")

    st.query_params.clear()
    st.rerun()


# =========================================================
# FORM DE IDENTIFICAÇÃO DO CLIENTE
# =========================================================
with st.form("client_form"):
    name = st.text_input("Nome completo", st.session_state.form_data["name"])
    email = st.text_input("E-mail", st.session_state.form_data["email"])

    submit = st.form_submit_button("Conectar conta")

if submit:
    if not name or not email:
        st.warning("Preencha todos os campos.")
        st.rerun()

    st.session_state.form_data = {"name": name, "email": email}

    try:
        token = create_connect_token(client_user_id=email)
        st.session_state.connect_token = token
    except Exception as e:
        st.error(f"Erro ao gerar token.")
        print("🔥 ERRO create_connect_token:", e)
        st.rerun()


# =========================================================
# ABRE O PLUGGY CONNECT (WIDGET)
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
            theme: "dark"
        }});
        connect.open();
    </script>
    """
    st.components.v1.html(html, height=600)
