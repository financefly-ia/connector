import streamlit as st
import sys, traceback

print("🚀 STEP 0: test_app_step iniciado", flush=True)

try:
    from modules.validator import startup_validation
    print("✅ STEP 1: Import validator OK", flush=True)
except Exception as e:
    print("🔥 ERRO import validator:", e, flush=True)
    traceback.print_exc()

try:
    from modules.pluggy import create_connect_token
    print("✅ STEP 2: Import pluggy OK", flush=True)
except Exception as e:
    print("🔥 ERRO import pluggy:", e, flush=True)
    traceback.print_exc()

try:
    from modules.db import save_client
    print("✅ STEP 3: Import db OK", flush=True)
except Exception as e:
    print("🔥 ERRO import db:", e, flush=True)
    traceback.print_exc()

st.title("Test App Step")
st.write("Se chegou até aqui, todos imports foram bem-sucedidos.")
print("✅ STEP 4: App carregou interface Streamlit com sucesso", flush=True)
