#!/bin/sh

echo "PORT env var from Railway: $PORT"
PORT=${PORT:-8080}

echo "Starting Streamlit + Health Server"

# Start health server in background ✅
python3 health_app.py &

# Now start streamlit ✅
exec streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
