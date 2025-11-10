# db.py
import os
import psycopg
from psycopg.rows import dict_row

# =========================================================
# Helper para carregar variáveis (Streamlit Cloud + Local)
# =========================================================
def get_env(key, default=None):
    # 1. Tenta pegar da env local (.env)
    val = os.getenv(key)
    if val:
        return val
    # 2. Se estiver rodando no Streamlit Cloud, tenta pegar dos secrets
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


# =========================================================
# Configuração do Banco de Dados
# =========================================================
DB_CONFIG = {
    "host": get_env("DB_HOST"),
    "port": get_env("DB_PORT"),
    "dbname": get_env("DB_NAME"),
    "user": get_env("DB_USER"),
    "password": get_env("DB_PASSWORD"),
    "sslmode": get_env("DB_SSLMODE", "require"),
}


# =========================================================
# Criação da tabela
# =========================================================
DDL = """
CREATE TABLE IF NOT EXISTS financefly_clients (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    item_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def get_conn():
    # Força timeout e SSL (Railway exige)
    return psycopg.connect(**DB_CONFIG, connect_timeout=10, target_session_attrs="read-write")


def init_db():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(DDL)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ init_db executado com sucesso")
    except Exception as e:
        print("🔥 ERRO init_db:", e)


def save_client(name, email, item_id):
    sql = """
    INSERT INTO financefly_clients (name, email, item_id)
    VALUES (%s, %s, %s)
    ON CONFLICT (item_id) DO NOTHING
    RETURNING id;
    """
    with get_conn() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (name, email, item_id))
        row = cur.fetchone()
        conn.commit()
        return row["id"] if row else None
