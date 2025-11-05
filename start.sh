#!/bin/bash

# Railway Streamlit Startup Script
# Provides robust startup mechanism with environment variable handling
# and fallback port configuration for Railway deployment

echo "Starting Financefly Connector Streamlit Application..."

# Export PORT environment variable with fallback to 8080
if [ -z "$PORT" ]; then
    echo "PORT environment variable not set, using fallback port 8080"
    export PORT=8080
else
    echo "Using Railway assigned PORT: $PORT"
fi

# Validate that PORT is numeric
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: PORT must be numeric, got: $PORT"
    echo "Falling back to default port 8080"
    export PORT=8080
fi

# Log startup configuration
echo "Configuration:"
echo "  PORT: $PORT"
echo "  SERVER_ADDRESS: 0.0.0.0"
echo "  HEADLESS_MODE: true"

# Start Streamlit with correct parameters for Railway deployment
echo "Launching Streamlit application..."
exec streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false