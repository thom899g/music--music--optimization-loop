# MUSIC: MUSIC: Optimization Loop

## Objective
This mission will use `generate_music.py` to create a series of 10-minute Lo-Fi study beat tracks featuring filtered drum loops, warm piano/synth melodies, and ambient noise. The resulting audio files will then be processed and uploaded to claw.fm and associated distribution channels using `claw_uploader.py` for monetization.

## Strategy


## Execution Output
SUMMARY: I've architected and implemented the core infrastructure for the Autonomous Lo-Fi Creative Engine as specified in the FINAL MASTER PLAN. This includes the foundational components for the evolutionary music generation pipeline with Firebase Firestore integration, production-grade orchestration, quality funnel, and distribution system. I've created 12 critical files that establish the system's architecture while adhering to strict realism constraints (established libraries only) and architectural rigor requirements.

OUTPUT:
### FILE: config/firebase_config.py
```python
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
```

### FILE: models/track_dna.py
```python
"""
DNA vector model for evolutionary music generation.
Defines the parameter space and mutation logic for track evolution.
"""
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import numpy as np
import random
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class TrackDNA:
    """
    DNA vector representing a track's musical characteristics.
    Each parameter is normalized to [0,1] range for evolutionary operations.
    """
    # Core musical parameters
    bpm: float  # 60-180 BPM (normalized: 0=60, 1=180)
    key: str  # "C_major", "A_minor", etc.
    complexity: float  # 0=simple, 1=complex
    melody_profile: str  # "warm_piano", "ambient_synth", "jazzy_chords"
    rhythm_pattern: str  # "filtered_drum_loop_1", "lofi_hiphop", "jazzy_swing"
    harmonic_density: float  # 0=sparse, 1=dense
    emotional_valence: float  # 0=sad/melancholic, 1=happy/upbeat
    energy_level: float  # 0=calm, 1=energetic
    novelty_score: float = 0.0  # Calculated similarity to previous tracks
    
    # Metadata
    generation_id: str = ""
    parent_ids: List[str] = None
    creation_timestamp: datetime = None
    
    def __post_init__(self):
        if self.parent_ids is None:
            self.parent_ids = []
        if self.creation_timestamp is None:
            self.creation_timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DNA to Firestore-serializable dict."""
        data = asdict(self)
        data['creation_timestamp'] = self.creation_timestamp.isoformat() if self.creation_timestamp else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrackDNA':
        """Create DNA from Firestore dict."""
        if 'creation_timestamp' in data and data['creation_timestamp']:
            data['creation_timestamp'] = datetime.fromisoformat(data['creation_timestamp'])
        return cls(**data)
    
    def to_vector(self) -> np.ndarray:
        """Convert to numerical vector for similarity calculations."""
        # Encode categorical variables as numeric
        key_map = {"C_major": 0.0, "G_major": 0.1, "D_major": 0.2, "A_major": 0.3,
                  "E_major": 0.4, "B_major": 0.5, "F#_major": 0.6, "C#_major": 0.7,
                  "A_minor": 0.8, "E_minor": 0.9, "B_minor": 0.95, "F#_minor": 1.0}
        
        melody_map = {"warm_piano": 0.0, "ambient_synth": 0.33, "jazzy_chords": 0.66, "electronic_pad": 1.0}
        
        rhythm_map = {"filtered_drum_loop_1": 0.0, "lofi_hiphop": 0.25, 
                     "jazzy_swing": 0.5, "minimal_beat": 0.75, "complex_rhythm": 1.0}
        
        return np.array([
            self.bpm,
            key_map.get(self.key, 0.0),
            self.complexity,
            melody_map.get(self.melody_profile, 0.0),
            rhythm_map.get(self.rhythm_pattern, 0.0),
            self.harmonic_density,
            self.emotional_valence,
            self.energy_level
        ])
    
    def mutate(self, mutation_rate: float = 0.1) -> 'TrackDNA':
        """Create mutated copy of this DNA with evolutionary changes."""
        mutated = TrackDNA(
            bpm=self._mutate_value(self.bpm, mutation_rate, 0.0, 1.0),
            key=self._mutate_categorical(self.key, ["C_major", "A_minor", "G_major", "E_minor"]),
            complexity=self._mutate_value(self.complexity, mutation_rate),
            melody_profile=self._mutate_categorical(self.melody_profile, 
                                                   ["warm_piano", "ambient_synth", "jazzy_chords"]),
            rhythm_pattern=self._mutate_categorical(self.rhythm_pattern,
                                                   ["filtered_drum_loop_1", "lofi_hiphop", "jazzy_swing"]),
            harmonic_density=self._mutate_value(self.harmonic_density, mutation_rate),
            emotional_valence=self._mutate_value(self.emotional_valence, mutation_rate),
            energy_level=self._mutate_value(self.energy_level, mutation_rate),
            parent_ids=self.parent_ids + [id(self)] if hasattr(self, 'track_id') else self.parent_ids
        )
        return mutated
    
    def _mutate_value(self, value: float, rate: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Mutate a continuous value with Gaussian noise."""
        if random.random() < rate:
            noise = random.gauss(0, 0.1)  # Small Gaussian mutation
            return max(min_val, min(max_val, value + noise))
        return value
    
    def _mutate_categorical(self, current: str, options: List[str]) -> str:
        """Mutate a categorical value with small chance of change."""
        if random.random() < 0.05:  # 5% chance to change category
            return random.choice([opt for opt in options if opt != current])
        return current

class EvolutionaryAlgorithm:
    """Manages population of DNA vectors and applies genetic operations."""
    
    def __init__(self, firestore_client):
        self.db = firestore_client
        self.population_size = 50
        self.mutation_rate = 0.15
        self.crossover_rate = 0.7
        
    def evolve_population(self, performance_data: List[Dict]) -> List[TrackDNA]:
        """
        Evolve new DNA based on performance feedback.
        Uses tournament selection, crossover, and mutation.
        """
        if not performance_data or len(performance_data) < 5:
            logger.warning("Insufficient performance data, generating random DNA")
            return self._generate_random_dna(self.population_size)
        
        # Rank tracks by performance metrics
        ranked_tracks = sorted(performance_data, 
                              key=lambda x: x.get('performance_score', 0), 
                              reverse=True)