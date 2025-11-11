#!/bin/sh

echo "PORT env var from Railway: $PORT"
PORT=${PORT:-8080}

echo "Starting Streamlit app on Railway..."
exec streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
