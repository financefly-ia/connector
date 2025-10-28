# app.py
import os
import requests
import streamlit as st
import traceback
import base64
from dotenv import load_dotenv
from db import init_db, save_client

# =========================================================
# CONFIGURAÇÃO INICIAL
# =========================================================
load_dotenv()
st.set_page_config(page_title="Financefly Connector", page_icon="🪁", layout="centered")

PLUGGY_CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID")
PLUGGY_CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET")
PLUGGY_BASE_URL = "https://api.pluggy.ai"

# =========================================================
# FUNÇÃO PARA CRIAR TOKEN DE CONEXÃO PLUGGY (CORRIGIDA)
# =========================================================
import requests

def create_connect_token(client_user_id=None):
    # 1️⃣ Autentica e gera o apiKey
    auth_resp = requests.post(
        "https://api.pluggy.ai/auth",
        headers={"Content-Type": "application/json"},
        json={
            "clientId": os.getenv("PLUGGY_CLIENT_ID"),
            "clientSecret": os.getenv("PLUGGY_CLIENT_SECRET")
        },
    )
    if auth_resp.status_code != 200:
        st.error(f"Erro ao autenticar com Pluggy: {auth_resp.status_code} - {auth_resp.text}")
        auth_resp.raise_for_status()

    api_key = auth_resp.json().get("apiKey")

    # 2️⃣ Usa o apiKey pra gerar o connect_token
    url = "https://api.pluggy.ai/connect_token"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {"clientUserId": client_user_id} if client_user_id else {}

    token_resp = requests.post(url, headers=headers, json=payload)
    if token_resp.status_code != 200:
        st.error(f"Erro ao gerar connect_token: {token_resp.status_code} - {token_resp.text}")
        token_resp.raise_for_status()

    return token_resp.json()["accessToken"]

# =========================================================
# ESTADO INICIAL DO APP
# =========================================================
if "connect_token" not in st.session_state:
    st.session_state.connect_token = None
if "form_data" not in st.session_state:
    st.session_state.form_data = {"name": "", "email": ""}

# =========================================================
# CONEXÃO COM O BANCO
# =========================================================
try:
    init_db()
except Exception as e:
    st.error(f"Erro ao conectar no banco: {e}")
    st.code(traceback.format_exc())

# =========================================================
# INTERFACE STREAMLIT
# =========================================================
st.title("Financefly Connector")
st.caption("Conecte sua conta bancária via Pluggy com segurança.")

# ---------------------------------------------------------
# CAPTURA DE PARAMETRO itemId PELA NOVA API
# ---------------------------------------------------------
params = st.query_params
item_id = params.get("itemId", None)

if item_id:
    name = st.session_state.form_data.get("name")
    email = st.session_state.form_data.get("email")

    if name and email:
        try:
            save_client(name, email, item_id)
            st.success(f"Conta conectada com sucesso! itemId: {item_id}")
        except Exception as e:
            st.error(f"Erro ao salvar no banco: {e}")
    else:
        st.warning("itemId recebido, mas faltam nome e e-mail.")

    st.query_params.clear()
    st.stop()

# ---------------------------------------------------------
# FORMULÁRIO DE CADASTRO
# ---------------------------------------------------------
with st.form("client_form"):
    name = st.text_input("Nome completo", st.session_state.form_data["name"])
    email = st.text_input("E-mail", st.session_state.form_data["email"])
    submit = st.form_submit_button("Conectar conta")

if submit:
    if not name or not email:
        st.warning("Preencha todos os campos.")
        st.stop()
    st.session_state.form_data = {"name": name, "email": email}

    try:
        token = create_connect_token(client_user_id=email)
        st.session_state.connect_token = token
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao gerar token Pluggy: {e}")
        st.code(traceback.format_exc())
        st.stop()

# ---------------------------------------------------------
# PLUGGY CONNECT WIDGET
# ---------------------------------------------------------
if st.session_state.connect_token:
    st.info("Abrindo o Pluggy Connect…")
    html = f"""
    <script src="https://cdn.pluggy.ai/pluggy-connect/v2.6.0/pluggy-connect.js"></script>
    <script>
      const connect = new PluggyConnect({{
        connectToken: "{st.session_state.connect_token}",
        includeSandbox: false,
        language: "pt",
        theme: "dark",
        onSuccess: (data) => {{
          const itemId = data?.item?.id;
          if (itemId) {{
            const url = new URL(window.location.href);
            url.searchParams.set("itemId", itemId);
            window.location.href = url.toString();
          }}
        }},
      }});
      connect.open();
    </script>
    """
    st.components.v1.html(html, height=10)
