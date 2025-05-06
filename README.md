# Self-Hosted RAG: Code-Aware AI Assistant

A fully self-hosted Retrieval-Augmented Generation (RAG) system that understands your codebase and provides intelligent responses to your code-related questions. All components run locally - no data leaves your machine.

## Features

- **Code-Aware AI**: Ask questions about your codebase and get intelligent responses
- **Fully Self-Hosted**: All components run locally with no external API calls
- **Docker-Based**: Easy deployment using Docker and docker-compose
- **Microservice Architecture**: Modular design for flexibility and scalability
- **Privacy-First**: Your code never leaves your machine
- **Web UI**: Simple web interface for interacting with the system

## Architecture

The system is composed of the following containerized components:

1. **Vector Database** (Qdrant): Stores code embeddings for semantic search
2. **Code Indexer**: Processes your codebase and creates searchable embeddings
3. **LLM Service** (Ollama): Runs a local language model for generating responses
4. **Query Service**: Connects all components and handles user queries
5. **Web UI**: Provides a simple interface for users

## Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 16GB RAM (32GB recommended)
- 10GB+ free disk space

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/choudharyr/code-compass.git
   cd self-hosted-rag
   ```

2. Create a directory structure for your code repositories
   ```bash
   mkdir -p repos
   ```

3. Copy your code repositories to the `repos` directory
   ```bash
   cp -r /path/to/your/codebase repos/
   ```

4. Start the services
   ```bash
   docker-compose up -d
   ```

5. Index your code
   ```bash
   docker-compose up code_indexer
   ```

6. Access the web UI at [http://localhost:8080](http://localhost:8080)

## 💬 Usage

1. Wait for all services to start (check with `docker-compose ps`)
2. Open the web UI at [http://localhost:8080](http://localhost:8080)
3. Ask questions about your codebase, such as:
   - "What does the function X do?"
   - "Explain the architecture of this codebase"
   - "How can I refactor this module?"
   - "How might I break down this monolith into microservices?"

## ⚙️ Configuration

Edit the `config/config.yaml` file to adjust settings:

```yaml
# Vector Database Configuration
qdrant:
  url: qdrant
  port: 6333
  collection_name: code_repository

# Embedding Model Configuration
embedding_model: BAAI/bge-base-en-v1.5

# LLM Configuration 
ollama_host: self-hosted-rag-ollama
ollama_model: mistral:7b-instruct

# Query Service Configuration
query_service:
  max_context_length: 4000
  default_top_k: 5
```

## Performance Considerations

- First query after startup may take several minutes as the LLM loads
- Subsequent queries are much faster
- CPU-only systems work but are significantly slower than GPU-equipped systems
- For better performance on CPU-only systems, consider using quantized models like `mistral:7b-instruct-q4_0`

## Extending the System

### Adding Jira/Confluence Integration

The system can be extended to include Jira and Confluence data by creating additional indexers that:

1. Connect to their respective APIs
2. Extract and process the content
3. Store embeddings in separate collections
4. Modify the query service to incorporate these data sources

### Supporting Microservice Analysis

A specialized prompt is included for analyzing monolithic applications and suggesting microservice decomposition. Use the "Microservice Analysis" option in the web UI.

## Troubleshooting

### Common Issues

1. **Container fails to start**: Check logs with `docker-compose logs [service_name]`
2. **Timeout errors**: Adjust timeout settings in nginx config and query service
3. **Model loading errors**: Ensure your system has enough RAM (16GB minimum, 32GB recommended)
4. **404 errors from LLM**: Verify the model name in config matches what's available in Ollama

## Security Considerations

This system is designed for internal use within trusted networks. It does not include authentication or TLS encryption. For production use, consider adding:

1. Authentication to the web UI and API
2. TLS encryption for all services
3. Network isolation for the Docker containers

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Qdrant](https://qdrant.tech/) for the vector database
- [Ollama](https://ollama.ai/) for the local LLM runtime
- [SentenceTransformers](https://www.sbert.net/) for embedding models
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [Bootstrap](https://getbootstrap.com/) for the UI components
