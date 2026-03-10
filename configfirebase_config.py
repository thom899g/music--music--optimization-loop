"""
Firebase configuration and Firestore client initialization.
Centralized Firestore client with proper error handling and connection pooling.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from google.cloud import firestore
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseManager:
    """Singleton Firebase client manager with connection pooling and error handling."""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._client = self._initialize_firestore()
    
    def _initialize_firestore(self) -> Optional[firestore.Client]:
        """
        Initialize Firestore client with credentials from environment or file.
        Handles multiple credential source fallbacks.
        """
        credential_paths = [
            os.getenv('FIREBASE_CREDENTIALS_PATH'),
            'config/firebase_credentials.json',
            'firebase_credentials.json'
        ]
        
        credentials = None
        
        # Try service account JSON first
        for path in credential_paths:
            if path and os.path.exists(path):
                try:
                    credentials = service_account.Credentials.from_service_account_file(path)
                    logger.info(f"Loaded Firebase credentials from {path}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load credentials from {path}: {e}")
        
        # Fallback to environment variable
        if credentials is None:
            firebase_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            if firebase_json:
                try:
                    service_account_info = json.loads(firebase_json)
                    credentials = service_account.Credentials.from_service_account_info(service_account_info)
                    logger.info("Loaded Firebase credentials from environment variable")
                except Exception as e:
                    logger.error(f"Failed to parse Firebase JSON from env: {e}")
        
        if credentials is None:
            logger.error("No Firebase credentials found. Check config/firebase_credentials.json or FIREBASE_SERVICE_ACCOUNT_JSON env var")
            return None
        
        try:
            client = firestore.Client(credentials=credentials, project=credentials.project_id)
            logger.info(f"Firestore client initialized for project: {credentials.project_id}")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            return None
    
    @property
    def client(self) -> firestore.Client:
        """Get Firestore client with lazy initialization."""
        if self._client is None:
            self._client = self._initialize_firestore()
        return self._client
    
    def get_collection(self, collection_name: str) -> firestore.CollectionReference:
        """Safely get collection reference with null check."""
        client = self.client
        if client is None:
            raise ConnectionError("Firestore client not initialized")
        return client.collection(collection_name)

# Singleton instance
firebase_manager = FirebaseManager()