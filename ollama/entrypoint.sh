#!/bin/bash

# Start Ollama service in the background
ollama serve &

# Wait for Ollama service to start
sleep 5

# Pull recommended models
if [ -n "$OLLAMA_MODELS" ]; then
    IFS=',' read -ra MODELS <<< "$OLLAMA_MODELS"
    for model in "${MODELS[@]}"; do
        echo "Pulling model: $model"
        ollama pull $model
    done
fi

# Keep container running
tail -f /dev/null