import os

def startup_validation():
    required_vars = ["PLUGGY_CLIENT_ID", "PLUGGY_CLIENT_SECRET", "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]

    for var in required_vars:
        if not os.getenv(var):
            raise RuntimeError(f"Variável de ambiente faltando: {var}")

    print("✅ Environment OK")
