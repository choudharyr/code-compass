FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements-query.txt .
RUN pip install --no-cache-dir -r requirements-query.txt

#RUN pip install --no-cache-dir numpy nltk && \
#    pip install --no-cache-dir huggingface-hub==0.17.3 && \
#    pip install --no-cache-dir torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu && \
#    pip install --no-cache-dir --no-deps sentence-transformers==2.2.2 && \
#    pip install --no-cache-dir fastapi==0.110.0 uvicorn==0.27.0 httpx==0.26.0 pydantic==2.5.3 qdrant-client==1.7.0 pyyaml==6.0

# Copy application files
COPY query_service.py .
COPY prompts.py .
COPY config.py .

# Create volume for configuration
VOLUME /config

# Expose API port
EXPOSE 8000

# Start the FastAPI service
CMD ["uvicorn", "query_service:app", "--host", "0.0.0.0", "--port", "8000"]