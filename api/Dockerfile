FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Descargar modelo spaCy
RUN pip install es-core-news-sm
#RUN pip install https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.7.1/es_core_news_sm-3.7.1-py3-none-any.whl
#RUN python -m spacy download es_core_news_sm

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 5000

# Comando de inicio
CMD ["python", "app.py"]
