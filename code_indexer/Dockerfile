FROM python:3.10-slim

WORKDIR /app

# Install git and required dependencies
RUN apt-get update && apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
#RUN pip install --no-cache-dir numpy nltk && \
#    pip install --no-cache-dir huggingface-hub==0.17.3 && \
#    pip install --no-cache-dir torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu && \
#    pip install --no-cache-dir sentence-transformers==2.2.2 && \
#    pip install --no-cache-dir qdrant-client==1.7.0 pyyaml==6.0 gitpython==3.1.40


# Copy indexing code
COPY code_indexer.py .
COPY chunking_utils.py .
COPY config.py .

# Mount points for code repositories
VOLUME /repos
# Mount point for configuration
VOLUME /config

CMD ["python", "code_indexer.py"]