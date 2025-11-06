#!/bin/sh

echo "Starting Streamlit app on Railway..."

# Define porta padrão
if [ -z "$PORT" ]; then
  PORT=8080
  echo "PORT not set. Using fallback 8080."
else
  echo "Received PORT=$PORT"
fi

# Validar se PORT é número
case $PORT in
  ''|*[!0-9]*)
    echo "Invalid PORT=$PORT. Falling back to 8080."
    PORT=8080
    ;;
esac

echo "Using port: $PORT"

# Rodar Streamlit
exec streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
