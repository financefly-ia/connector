# app.py
import os
import sys
import logging
from datetime import datetime

# =========================================================
# ENHANCED LOGGING CONFIGURATION
# =========================================================
# Configure logging for deployment validation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_startup_info(message, level="INFO"):
    """Enhanced logging function for startup validation"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"[RAILWAY {level}] {timestamp}"
    print(f"{prefix} {message}")
    if level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)

# =========================================================
# RAILWAY DEPLOYMENT CONFIGURATION
# =========================================================
# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

log_startup_info("=== RAILWAY DEPLOYMENT STARTUP VALIDATION ===")
log_startup_info("Starting enhanced port configuration and validation...")

# Configure Streamlit server settings for Railway deployment
port = os.getenv("PORT")
log_startup_info(f"Environment variable $PORT: {port}")

# Enhanced port configuration with detailed logging
if port is None:
    log_startup_info("$PORT environment variable not found", "WARNING")
    log_startup_info("Using fallback port 8080 for local/development environment")
    port = "8080"
else:
    log_startup_info(f"Railway assigned dynamic port: {port}")

# Enhanced port validation with detailed error handling
try:
    port_num = int(port)
    if port_num < 1 or port_num > 65535:
        raise ValueError(f"Port {port_num} is outside valid range (1-65535)")
    log_startup_info(f"Port validation successful: {port_num}")
    log_startup_info(f"Application will bind to port {port_num}")
except ValueError as e:
    log_startup_info(f"Port validation failed: {e}", "ERROR")
    log_startup_info("Falling back to default port 8080", "WARNING")
    port = "8080"
    port_num = 8080

# Set Streamlit server environment variables for Railway compatibility
log_startup_info("Configuring Streamlit server environment variables...")
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_SERVER_PORT"] = str(port)
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"

log_startup_info("=== FINAL SERVER CONFIGURATION ===")
log_startup_info(f"Server Port: {port}")
log_startup_info(f"Server Address: 0.0.0.0 (external access enabled)")
log_startup_info(f"Headless Mode: true (server deployment)")
log_startup_info(f"Expected Network URL: http://0.0.0.0:{port}")

# Enhanced environment variable validation with detailed reporting
log_startup_info("=== ENVIRONMENT VARIABLE VALIDATION ===")
required_vars = {
    "PLUGGY_CLIENT_ID": "Pluggy API authentication",
    "PLUGGY_CLIENT_SECRET": "Pluggy API authentication", 
    "DB_HOST": "PostgreSQL database host",
    "DB_USER": "PostgreSQL database user",
    "DB_PASSWORD": "PostgreSQL database password",
    "DB_NAME": "PostgreSQL database name"
}

missing_vars = []
present_vars = []

for var, description in required_vars.items():
    value = os.getenv(var)
    if not value:
        missing_vars.append(var)
        log_startup_info(f"❌ {var}: MISSING - {description}", "ERROR")
    else:
        present_vars.append(var)
        # Log partial value for security (don't expose full credentials)
        if "SECRET" in var or "PASSWORD" in var:
            masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            log_startup_info(f"✅ {var}: PRESENT - {description} (value: {masked_value})")
        else:
            log_startup_info(f"✅ {var}: PRESENT - {description} (value: {value})")

# Optional environment variables
optional_vars = {
    "DB_PORT": os.getenv("DB_PORT", "5432"),
    "DB_SSLMODE": os.getenv("DB_SSLMODE", "require")
}

log_startup_info("=== OPTIONAL ENVIRONMENT VARIABLES ===")
for var, default_value in optional_vars.items():
    actual_value = os.getenv(var, default_value)
    log_startup_info(f"📋 {var}: {actual_value} {'(default)' if actual_value == default_value else '(configured)'}")

# Summary of environment validation
if missing_vars:
    log_startup_info(f"❌ VALIDATION FAILED: {len(missing_vars)} required variables missing: {missing_vars}", "ERROR")
    log_startup_info("Application may not function correctly without these variables", "ERROR")
else:
    log_startup_info(f"✅ VALIDATION PASSED: All {len(required_vars)} required environment variables present")

log_startup_info(f"Environment validation complete: {len(present_vars)}/{len(required_vars)} required variables present")

# =========================================================
# DEPLOYMENT READINESS VALIDATION
# =========================================================
log_startup_info("=== RUNNING DEPLOYMENT READINESS VALIDATION ===")

try:
    from modules.deployment_validator import run_deployment_validation
    
    # Run comprehensive deployment validation
    validation_results = run_deployment_validation()
    
    # Store validation results for potential UI display
    deployment_ready = validation_results.get("overall", False)
    validation_errors = validation_results.get("errors", [])
    validation_warnings = validation_results.get("warnings", [])
    
    if deployment_ready:
        log_startup_info("🎉 DEPLOYMENT VALIDATION PASSED - Application ready for production")
    else:
        log_startup_info("⚠️ DEPLOYMENT VALIDATION FAILED - Issues detected", "ERROR")
        log_startup_info(f"Errors: {len(validation_errors)}, Warnings: {len(validation_warnings)}", "ERROR")
        
        # Continue execution but log the issues
        for error in validation_errors[:5]:  # Limit to first 5 errors
            log_startup_info(f"Critical: {error}", "ERROR")
            
except Exception as e:
    log_startup_info(f"❌ Deployment validation failed to run: {e}", "ERROR")
    log_startup_info("Continuing with application startup...", "WARNING")

import requests
import streamlit as st
import traceback
from modules.db import init_db, save_client

# =========================================================
# CONFIGURAÇÃO INICIAL
# =========================================================
requests.adapters.DEFAULT_RETRIES = 3
st.set_page_config(page_title="Financefly Connector", page_icon="🪁", layout="centered")

PLUGGY_CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID")
PLUGGY_CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET")
PLUGGY_BASE_URL = "https://api.pluggy.ai"

# Enhanced Pluggy API configuration validation
log_startup_info("=== PLUGGY API CONFIGURATION VALIDATION ===")
if PLUGGY_CLIENT_ID and PLUGGY_CLIENT_SECRET:
    log_startup_info(f"✅ Pluggy API credentials configured")
    log_startup_info(f"Client ID: {PLUGGY_CLIENT_ID[:8]}...{PLUGGY_CLIENT_ID[-4:]} (masked)")
    log_startup_info(f"Client Secret: {'*' * (len(PLUGGY_CLIENT_SECRET) - 8)}{PLUGGY_CLIENT_SECRET[-4:]} (masked)")
    log_startup_info(f"Pluggy Base URL: {PLUGGY_BASE_URL}")
else:
    log_startup_info("❌ Pluggy API credentials not found", "ERROR")
    if not PLUGGY_CLIENT_ID:
        log_startup_info("Missing PLUGGY_CLIENT_ID environment variable", "ERROR")
    if not PLUGGY_CLIENT_SECRET:
        log_startup_info("Missing PLUGGY_CLIENT_SECRET environment variable", "ERROR")

# =========================================================
# FUNÇÃO PARA CRIAR TOKEN DE CONEXÃO PLUGGY
# =========================================================
def create_connect_token(client_user_id=None):
    auth_resp = requests.post(
        f"{PLUGGY_BASE_URL}/auth",
        headers={"accept": "application/json", "content-type": "application/json"},
        json={"clientId": PLUGGY_CLIENT_ID, "clientSecret": PLUGGY_CLIENT_SECRET},
        timeout=15
    )

    if auth_resp.status_code != 200:
        st.error(f"Erro ao autenticar com Pluggy: {auth_resp.status_code} - {auth_resp.text}")
        auth_resp.raise_for_status()

    api_key = auth_resp.json().get("apiKey")
    if not api_key:
        raise ValueError("API key não recebida na resposta da Pluggy")

    url = f"{PLUGGY_BASE_URL}/connect_token"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": api_key
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
# DATABASE SCHEMA INITIALIZATION
# =========================================================
log_startup_info("=== DATABASE SCHEMA INITIALIZATION ===")

try:
    # Initialize database schema (connection already validated above)
    log_startup_info("Initializing database schema...")
    init_db()
    log_startup_info("✅ Database schema initialization successful")
    
except Exception as e:
    log_startup_info(f"❌ Database schema initialization failed: {str(e)}", "ERROR")
    st.error(f"❌ Database initialization failed: {e}")
    st.error("Please check the database configuration and try again.")
    st.code(traceback.format_exc())

# =========================================================
# INTERFACE STREAMLIT
# =========================================================
st.title("Financefly Connector")
st.caption("Conecte sua conta bancária via Pluggy com segurança.")

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

# =========================================================
# FORMULÁRIO DE CADASTRO
# =========================================================
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

# =========================================================
# PLUGGY CONNECT WIDGET
# =========================================================
if st.session_state.connect_token:
    st.info("Abrindo o Pluggy Connect…")

    html = f"""
    <div id="pluggy-status" style="margin:8px 0; font-family: ui-sans-serif, system-ui;">
      Token pronto (parcial): <code>{st.session_state.connect_token[:8]}...</code>
    </div>

    <script>
      (async function() {{
        const statusEl = document.getElementById('pluggy-status');
        function log(msg) {{
          const p = document.createElement('div');
          p.textContent = msg;
          statusEl.appendChild(p);
        }}

        log("Carregando SDK Pluggy diretamente...");

        // Baixa o SDK via fetch e insere no DOM manualmente
        try {{
          const sdkResp = await fetch("https://cdn.pluggy.ai/pluggy-connect/v2.9.2/pluggy-connect.js");
          if (!sdkResp.ok) throw new Error("Falha ao buscar SDK Pluggy");
          const sdkText = await sdkResp.text();
          const scriptEl = document.createElement("script");
          scriptEl.textContent = sdkText;
          document.body.appendChild(scriptEl);
          log("SDK Pluggy injetado com sucesso!");
        }} catch (e) {{
          log("Erro ao baixar SDK: " + e.message);
          return;
        }}

        try {{
          const connect = new PluggyConnect({{
            connectToken: "{st.session_state.connect_token}",
            includeSandbox: false,
            language: "pt",
            theme: "dark",
            onOpen: () => log("Pluggy Connect aberto."),
            onClose: () => log("Pluggy Connect fechado."),
            onError: (err) => log("Erro do Pluggy: " + JSON.stringify(err))
          }});
          connect.open();
        }} catch (e) {{
          log("Exceção ao abrir Connect: " + (e?.message || e));
        }}
      }})();
    </script>
    """
    st.components.v1.html(html, height=600, scrolling=False)

