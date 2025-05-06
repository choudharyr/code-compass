"""
Query service API - connects vector database with LLM for code-aware responses
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from config import load_config
from prompts import SYSTEM_PROMPT_TEMPLATE, MICROSERVICE_ANALYSIS_PROMPT

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Code-Aware RAG API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Global variables for clients
embedding_model = None
qdrant_client = None
config = None

class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    top_k: int = 5
    task_type: Optional[str] = None  # For specialized tasks like "microservice_analysis"

class QueryResponse(BaseModel):
    """Query response model"""
    answer: str
    sources: List[Dict[str, Any]]

@app.on_event("startup")
async def startup():
    """Initialize clients on startup"""
    global embedding_model, qdrant_client, config
    
    # Load configuration
    config = load_config()
    
    # Initialize embedding model
    logger.info(f"Loading embedding model: {config['embedding_model']}")
    embedding_model = SentenceTransformer(config['embedding_model'])
    
    # Initialize Qdrant client
    logger.info(f"Connecting to Qdrant at {config['qdrant']['url']}:{config['qdrant']['port']}")
    qdrant_client = QdrantClient(
        url=config['qdrant']['url'],
        port=config['qdrant']['port']
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "online", "service": "Code-Aware RAG API"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query endpoint that combines retrieval with generation"""
    try:
        # Generate embedding for the query
        query_embedding = embedding_model.encode(request.query)
        
        # Search Qdrant for similar code snippets
        search_result = qdrant_client.search(
            collection_name=config['qdrant']['collection_name'],
            query_vector=query_embedding.tolist(),
            limit=request.top_k
        )
        
        # Extract retrieved code contexts
        contexts = []
        sources = []
        
        for result in search_result:
            contexts.append(result.payload["text"])
            sources.append({
                "text": result.payload["text"][:200] + "...",  # Preview
                "file_path": result.payload["file_path"],
                "repo_name": result.payload["repo_name"],
                "score": round(result.score, 3)
            })
        
        # Create prompt based on task type
        prompt = ""
        if request.task_type == "microservice_analysis":
            # Special prompt for microservice decomposition analysis
            prompt = MICROSERVICE_ANALYSIS_PROMPT.format(
                query=request.query,
                contexts="\n\n---\n\n".join(contexts)
            )
        else:
            # Standard code-aware prompt
            prompt = SYSTEM_PROMPT_TEMPLATE.format(
                query=request.query,
                contexts="\n\n---\n\n".join(contexts)
            )
        
        # Call Ollama API for generation
        ollama_url = f"http://{config.get('ollama_host', 'ollama')}:11434/api/generate"
        logger.info(f"Connecting to Ollama at: {ollama_url}")
        
        async with httpx.AsyncClient(timeout=600.0) as client:  # Increase timeout to 10 minutes
            try:
                # First, try to ping the Ollama service
                ping_response = await client.head(f"http://{config.get('ollama_host', 'ollama')}:11434")
                logger.info(f"Ollama ping response: {ping_response.status_code}")
            except Exception as e:
                logger.warning(f"Failed to ping Ollama: {e}")
                
            # Now try the actual generation request
            response = await client.post(
                ollama_url,
                json={
                    "model": config.get('ollama_model', 'codellama'),
                    "prompt": prompt,
                    "temperature": 0.1,  # Low temperature for more deterministic responses
                    "max_tokens": 1024,  # Reduced from 2048 to lower generation time
                    "num_ctx": 2048,     # Explicitly set context window to smaller value
                    "stream": False      # Disable streaming to get a single response
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Error calling LLM API: Status {response.status_code}, Response: {response.text}")
                raise HTTPException(status_code=500, detail=f"Error calling LLM API: {response.status_code}")
                
            # Extract the generated text
            try:
                # Try to parse as JSON
                llm_response = response.json()
                answer = llm_response.get("response", "")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {e}")
                # If JSON parsing fails, try to extract the response from the text
                try:
                    # The response might be streaming format with multiple JSON objects
                    # Let's try to parse the first complete JSON object
                    text = response.text.strip()
                    if text:
                        # Find the first complete JSON object
                        first_json_obj = text.split("\n")[0]
                        llm_response = json.loads(first_json_obj)
                        answer = llm_response.get("response", "")
                    else:
                        answer = "Failed to generate response from the model."
                except Exception as parse_err:
                    logger.error(f"Error extracting response from text: {parse_err}")
                    answer = "Error processing model response."
            
            return {
                "answer": answer,
                "sources": sources
            }
            
    except httpx.TimeoutException as e:
        logger.error(f"Timeout calling LLM API: {e}")
        raise HTTPException(status_code=504, detail="LLM API request timed out. The model may need more time to generate a response.")
    except httpx.ConnectError as e:
        logger.error(f"Connection error to LLM API: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to LLM API. Please check if Ollama service is running.")
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # For local testing
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)