# Use uma imagem oficial do Python (escolhi 3.11-slim por compatibilidade com wheels)
FROM python:3.11-slim

# Instala dependências do sistema necessárias para Pillow e psycopg
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      gcc \
      libpq-dev \
      zlib1g-dev \
      libjpeg-dev \
      libfreetype6-dev \
      liblcms2-dev \
      libopenjp2-7-dev \
      libtiff5-dev \
      libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

# Cria diretório app
WORKDIR /app

# Copia requirements e instala (usa pip wheel cache e não roda streamlit como root)
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copia o código
COPY . .

# Expõe porta (opcional) — Railway injetará $PORT dinamicamente
EXPOSE 8501

# Comando default para rodar o Streamlit – usa a variável $PORT para compatibilidade com plataformas
# Usamos shell form via `sh -c` para expandir a variável de ambiente.
CMD ["sh", "-c", "streamlit run app.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true"]
