import streamlit as st
import sys

print("🚀 Debug inicial executado!", flush=True)

st.title("Debug App")
st.write("Se você está vendo isso, o Streamlit está executando normalmente.")

print("✅ Streamlit rodando código até o fim!", flush=True)
sys.stdout.flush()
