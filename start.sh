#!/bin/bash

echo "Starting Streamlit app on Railway..."

export PORT=${PORT:-8080}

if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "Invalid PORT: $PORT. Falling back to 8080."
    PORT=8080
fi

echo "Using port: $PORT"

streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
