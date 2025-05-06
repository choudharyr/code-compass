FROM ollama/ollama:latest

# Create a volume for model storage
VOLUME /root/.ollama

# Expose the Ollama API port
EXPOSE 11434

# Set recommended models to pull on startup
ENV OLLAMA_MODELS="qwen3:4b"

# Entrypoint script to pull models and start Ollama
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]