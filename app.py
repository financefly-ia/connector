# app.py
import os
import requests
import streamlit as st
import traceback
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
def create_connect_token(client_user_id=None):
    # 1️⃣ Autentica e obtém o apiKey
    auth_resp = requests.post(
        f"{PLUGGY_BASE_URL}/auth",
        headers={
            "accept": "application/json",
            "content-type": "application/json"
        },
        json={
            "clientId": PLUGGY_CLIENT_ID,
            "clientSecret": PLUGGY_CLIENT_SECRET
        },
        timeout=15
    )

    if auth_resp.status_code != 200:
        st.error(f"Erro ao autenticar com Pluggy: {auth_resp.status_code} - {auth_resp.text}")
        auth_resp.raise_for_status()

    api_key = auth_resp.json().get("apiKey")
    if not api_key:
        raise ValueError("API key não recebida na resposta da Pluggy")

    # 2️⃣ Usa o apiKey no header correto
    url = f"{PLUGGY_BASE_URL}/connect_token"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": api_key  # <<< Cabeçalho correto
    }
    payload = {"clientUserId": client_user_id} if client_user_id else {}

    token_resp = requests.post(url, headers=headers, json=payload, timeout=15)

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
item_id = params.get("itemId", [None])[0] if isinstance(params.get("itemId"), list) else params.get("itemId")

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
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        st.code(traceback.format_exc())
        st.stop()

# ---------------------------------------------------------
# PLUGGY CONNECT WIDGET
# ---------------------------------------------------------
if st.session_state.connect_token:
    st.info("Abrindo o Pluggy Connect…")
    token_mask = st.session_state.connect_token[:8] + "..."  # só pra debug leve no front

    html = f"""
    <div id="pluggy-status" style="margin:8px 0; font-family: ui-sans-serif, system-ui;">
      Token pronto (parcial): <code>{token_mask}</code>
    </div>

    <script src="https://cdn.pluggy.ai/pluggy-connect/v2.6.0/pluggy-connect.js"></script>
    <script>
      (function() {{
        const statusEl = document.getElementById('pluggy-status');

        function log(msg) {{
          if (statusEl) {{
            const p = document.createElement('div');
            p.textContent = msg;
            statusEl.appendChild(p);
          }}
        }}

        try {{
          const connect = new PluggyConnect({{
            connectToken: "{st.session_state.connect_token}",
            includeSandbox: false,
            language: "pt",
            theme: "dark",
            onOpen: () => log("Connect aberto."),
            onClose: () => log("Connect fechado."),
            onEvent: (evt) => log("Evento: " + JSON.stringify(evt)),
            onError: (err) => log("Erro do Pluggy: " + JSON.stringify(err))
          }});

          log("Instância criada, chamando open()...");
          connect.open();

        }} catch (e) {{
          log("Exceção ao criar/abrir Connect: " + (e?.message || e));
        }}
      }})();
    </script>
    """
    # Aumente a altura para o modal aparecer corretamente dentro do iframe
    st.components.v1.html(html, height=600, scrolling=False)
