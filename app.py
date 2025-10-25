# app.py
import streamlit as st
import traceback

# =========================================================
# CONFIGURAÇÃO INICIAL + BLOCO DE DIAGNÓSTICO
# =========================================================
st.set_page_config(page_title="Financefly Connector", page_icon="🪁", layout="centered")

st.title("🚀 Financefly Connector")
st.caption("Inicializando ambiente...")

try:
    import os
    import requests
    from dotenv import load_dotenv
    from db import init_db, save_client

    load_dotenv()
    st.success("✅ Módulos importados com sucesso.")
except Exception as e:
    st.error(f"❌ Falha ao importar módulos: {e}")
    st.code(traceback.format_exc())
    st.stop()

# =========================================================
# VARIÁVEIS DE AMBIENTE PLUGGY
# =========================================================
PLUGGY_CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID")
PLUGGY_CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET")
PLUGGY_BASE_URL = "https://api.pluggy.ai"

# =========================================================
# FUNÇÃO PARA CRIAR TOKEN DE CONEXÃO PLUGGY
# =========================================================
def create_connect_token(client_user_id=None):
    url = f"{PLUGGY_BASE_URL}/connect_token"
    payload = {"clientUserId": client_user_id} if client_user_id else {}
    resp = requests.post(url, json=payload, auth=(PLUGGY_CLIENT_ID, PLUGGY_CLIENT_SECRET))
    resp.raise_for_status()
    return resp.json()["accessToken"]

# =========================================================
# ESTADO INICIAL DO APP
# =========================================================
if "connect_token" not in st.session_state:
    st.session_state.connect_token = None
if "form_data" not in st.session_state:
    st.session_state.form_data = {"name": "", "email": ""}

# =========================================================
# CONEXÃO COM O BANCO DE DADOS
# =========================================================
# try:
  #  init_db()
   # st.info("💾 Banco inicializado com sucesso.")
# except Exception as e:
   # st.error(f"⚠️ Erro ao conectar no banco: {e}")
   # st.code(traceback.format_exc())
   # st.stop()

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
            st.code(traceback.format_exc())
    else:
        st.warning("itemId recebido, mas faltam nome e e-mail.")

    # Limpa os parâmetros da URL
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
    token = create_connect_token(client_user_id=email)
    st.session_state.connect_token = token

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
