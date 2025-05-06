"""
Code Indexer - Scans repositories, chunks code, and indexes in vector database
"""
import os
import glob
import logging
from pathlib import Path
import yaml
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException
from sentence_transformers import SentenceTransformer
from chunking_utils import chunk_code_file
from config import load_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_repository(repo_path, embedding_model, qdrant_client, collection_name):
    """Process a single code repository"""
    logger.info(f"Processing repository: {repo_path}")
    
    # Get all code files (extend this list as needed)
    code_extensions = ['.py', '.java', '.js', '.ts', '.go', '.rb', '.cs', '.cpp', '.c', '.h']
    code_files = []
    
    for ext in code_extensions:
        code_files.extend(glob.glob(f"{repo_path}/**/*{ext}", recursive=True))
    
    logger.info(f"Found {len(code_files)} code files")
    
    # Skip files in these directories
    excluded_dirs = ['node_modules', 'venv', '.git', '__pycache__', 'build', 'dist']
    
    # Process each file
    all_chunks = []
    file_metadata = []
    
    for file_path in code_files:
        # Skip excluded directories
        if any(excluded_dir in file_path for excluded_dir in excluded_dirs):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Get relative path within repository
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Chunk the file
            chunks = chunk_code_file(content, file_path)
            
            # Add metadata to each chunk
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                file_metadata.append({
                    "file_path": rel_path,
                    "repo_name": os.path.basename(repo_path),
                    "chunk_id": i,
                    "language": os.path.splitext(file_path)[1][1:],
                })
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    if not all_chunks:
        logger.warning("No code chunks were extracted")
        return
        
    # Create embeddings in batches
    batch_size = 32
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i+batch_size]
        batch_metadata = file_metadata[i:i+batch_size]
        
        # Generate embeddings
        embeddings = embedding_model.encode(batch_chunks)
        
        # Prepare points for Qdrant
        points = [
            models.PointStruct(
                id=i+j,
                vector=embedding.tolist(),
                payload={
                    "text": batch_chunks[j],
                    "file_path": batch_metadata[j]["file_path"],
                    "repo_name": batch_metadata[j]["repo_name"],
                    "chunk_id": batch_metadata[j]["chunk_id"],
                    "language": batch_metadata[j]["language"],
                }
            )
            for j, embedding in enumerate(embeddings)
        ]
        
        # Upsert to Qdrant
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        logger.info(f"Indexed batch {i//batch_size + 1}/{(len(all_chunks) + batch_size - 1)//batch_size}")

def main():
    """Main function to process repositories and index them"""
    # Load configuration
    config = load_config()
    
    # Connect to Qdrant
    qdrant_client = QdrantClient(
        url=config['qdrant']['url'],
        port=config['qdrant']['port']
    )
    
    collection_name = config['qdrant']['collection_name']
    
    # Load embedding model
    logger.info("Loading embedding model")
    embedding_model = SentenceTransformer(config['embedding_model'])
    
    # Get embedding dimension from the model
    test_embedding = embedding_model.encode("Test")
    embedding_dim = len(test_embedding)
    logger.info(f"Embedding dimension: {embedding_dim}")
    
    # Check if collection exists and has the right dimensions
    collections = qdrant_client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    recreate_collection = False
    if collection_name in collection_names:
        # Try to check collection info, but handle parsing errors
        try:
            collection_info = qdrant_client.get_collection(collection_name)
            # Check if the vector size is correct
            existing_dim = collection_info.config.params.vectors.size
            logger.info(f"Existing collection dimension: {existing_dim}")
            
            if existing_dim != embedding_dim:
                logger.warning(f"Dimension mismatch: collection has {existing_dim}, model produces {embedding_dim}")
                logger.warning("Recreating collection with correct dimensions")
                qdrant_client.delete_collection(collection_name)
                recreate_collection = True
                
        except ResponseHandlingException as e:
            # If we get a parsing error, it's safer to recreate the collection
            logger.warning(f"Could not parse collection info due to API compatibility issue: {e}")
            logger.warning("Recreating collection with correct dimensions")
            try:
                qdrant_client.delete_collection(collection_name)
            except Exception as del_err:
                logger.error(f"Error deleting collection: {del_err}")
            recreate_collection = True
            
        except Exception as e:
            logger.error(f"Error checking collection: {e}")
            recreate_collection = True
    else:
        logger.info(f"Collection {collection_name} doesn't exist")
        recreate_collection = True
    
    if recreate_collection:
        logger.info(f"Creating collection {collection_name} with dimension {embedding_dim}")
        try:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_dim,  # Use actual embedding dimension
                    distance=models.Distance.COSINE
                )
            )
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return
    
    # Process each repository
    for repo_path in config['repositories']:
        process_repository(repo_path, embedding_model, qdrant_client, collection_name)
    
    logger.info("Indexing complete")

if __name__ == "__main__":
    main()