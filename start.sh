#!/bin/sh

echo "PORT env var from Railway: $PORT"

# fallback porto
PORT=${PORT:-8080}

echo "Starting Streamlit app on Railway..."
echo "Received PORT=$PORT"
echo "Using port: $PORT"

exec streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
