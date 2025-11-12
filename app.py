import os
import streamlit as st

print("🧩 STEP 1: Iniciando importações...")

try:
    from modules.validator import startup_validation
    print("🧩 STEP 2: Import validator OK")
    from modules.pluggy import create_connect_token
    print("🧩 STEP 3: Import pluggy OK")
    from modules.db import save_client
    print("🧩 STEP 4: Import db OK")
except Exception as e:
    print(f"🔥 ERRO nos imports: {e}")

# =========================================================
# CONFIG STREAMLIT
# =========================================================
try:
    st.set_page_config(
        page_title="Financefly Connector",
        page_icon="💸",
        layout="centered"
    )
    print("🧩 STEP 5: Configuração do Streamlit OK")
except Exception as e:
    print(f"🔥 ERRO na configuração do Streamlit: {e}")

# =========================================================
# STARTUP SAFE
# =========================================================
try:
    with st.spinner("Inicializando ambiente..."):
        startup_validation()
    print("🧩 STEP 6: startup_validation() executado com sucesso")
except Exception as e:
    st.warning(f"Aviso durante inicialização: {e}")
    print(f"🔥 ERRO no startup_validation: {e}")

# =========================================================
# SESSION STATE
# =========================================================
try:
    if "connect_token" not in st.session_state:
        st.session_state.connect_token = None

    if "form_data" not in st.session_state:
        st.session_state.form_data = {"name": "", "email": ""}

    if "item_processed" not in st.session_state:
        st.session_state.item_processed = False

    print("🧩 STEP 7: Session state inicializado OK")
except Exception as e:
    print(f"🔥 ERRO no session_state: {e}")

# =========================================================
# VERIFICAÇÃO URL (itemId)
# =========================================================
try:
    params = st.query_params
    item_id = params.get("itemId") if params else None

    if item_id and not st.session_state.item_processed:
        print(f"🧩 STEP 8: itemId detectado → {item_id}")

        name = st.session_state.form_data.get("name", "")
        email = st.session_state.form_data.get("email", "")

        if name and email:
            try:
                save_client(name, email, item_id)
                st.success("Conta conectada com sucesso!")
                print("🧩 STEP 9: save_client() executado com sucesso")
            except Exception as e:
                st.error(f"Erro ao salvar no banco: {e}")
                print(f"🔥 ERRO save_client: {e}")
        else:
            st.warning("itemId recebido, mas nome/email não foram preenchidos.")
            print("⚠️ STEP 9.1: itemId recebido sem nome/email")

        st.session_state.item_processed = True
except Exception as e:
    print(f"🔥 ERRO na verificação de itemId: {e}")

# =========================================================
# UI / FORM
# =========================================================
try:
    st.title("Financefly Connector")
    st.caption("Conecte sua conta bancária via Pluggy com segurança.")
    print("🧩 STEP 10: UI carregada com sucesso")

    with st.form("client_form"):
        name = st.text_input("Nome completo", st.session_state.form_data["name"])
        email = st.text_input("E-mail", st.session_state.form_data["email"])
        submit = st.form_submit_button("Conectar conta")

    print("🧩 STEP 11: Form renderizado")
except Exception as e:
    print(f"🔥 ERRO ao renderizar formulário: {e}")

# =========================================================
# SUBMIT FORM
# =========================================================
try:
    if submit:
        print("🧩 STEP 12: Botão de submit clicado")
        if not name or not email:
            st.warning("Preencha todos os campos.")
            print("⚠️ STEP 12.1: Campos vazios detectados")
        else:
            st.session_state.form_data = {"name": name, "email": email}
            try:
                token = create_connect_token(client_user_id=email)
                st.session_state.connect_token = token
                print("🧩 STEP 13: Token Pluggy criado com sucesso")
            except Exception as e:
                st.error(f"Erro ao gerar token: {e}")
                print(f"🔥 ERRO create_connect_token: {e}")
except Exception as e:
    print(f"🔥 ERRO no bloco submit: {e}")

# =========================================================
# WIDGET PLUGGY
# =========================================================
try:
    if st.session_state.connect_token:
        st.info("Abrindo o Pluggy Connect…")
        print("🧩 STEP 14: Exibindo widget Pluggy")

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
        print("🧩 STEP 15: Widget Pluggy renderizado com sucesso")
except Exception as e:
    print(f"🔥 ERRO no widget Pluggy: {e}")

print("✅ FINAL: app.py carregado completamente com sucesso.")
