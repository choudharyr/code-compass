"""
Configuration loading module
"""
import os
import yaml
import logging

logger = logging.getLogger(__name__)

def load_config():
    """
    Load configuration from config.yaml file
    
    Returns:
        dict: Configuration dictionary
    """
    config_path = os.environ.get('CONFIG_PATH', '/config/config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Set defaults if not present
        config.setdefault('qdrant', {})
        config['qdrant'].setdefault('url', 'qdrant')
        config['qdrant'].setdefault('port', 6333)
        config['qdrant'].setdefault('collection_name', 'code_repository')
        
        config.setdefault('embedding_model', 'BAAI/bge-small-en-v1.5')
        
        # Set repository paths
        config.setdefault('repositories', ['/repos'])
        
        return config
        
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found, using defaults")
        
        # Return default configuration
        return {
            'qdrant': {
                'url': 'qdrant',
                'port': 6333,
                'collection_name': 'code_repository'
            },
            'embedding_model': 'BAAI/bge-small-en-v1.5',
            'repositories': ['/repos']
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise