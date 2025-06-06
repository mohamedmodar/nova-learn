# config.py
"""Configuration settings for the recommender system."""

import os

# --- Directory Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # recommender_system directory
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# --- File Paths ---
# Input data path (adjust if needed)
COURSE_DATA_PATH = "data/final(final).csv" # Adjusted to the provided dataset name

# Path for generated interaction data
INTERACTION_DATA_PATH = os.path.join(DATA_DIR, "fake_user_interactions.csv") # Added this line

# Paths for generated model components (will be updated by generation scripts)
TFIDF_VECTORIZER_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
TFIDF_MATRIX_PATH = os.path.join(MODEL_DIR, "tfidf_matrix.pkl")
SBERT_EMBEDDINGS_PATH = os.path.join(MODEL_DIR, "course_sbert_embeddings.pkl")
TWO_TOWER_MODEL_WEIGHTS_PATH = os.path.join(MODEL_DIR, "two_tower_model.weights.h5")

# --- Model Parameters ---
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"

# Two-Tower Model Parameters
TWO_TOWER_USER_EMBEDDING_DIM = 64
TWO_TOWER_ITEM_EMBEDDING_DIM = 64 # This should match SBERT output if using SBERT embeddings directly
TWO_TOWER_SHARED_EMBEDDING_DIM = 64 # Used if user/item towers share final projection
TWO_TOWER_LEARNING_RATE = 0.01
TWO_TOWER_EPOCHS = 10 # Adjust as needed
TWO_TOWER_BATCH_SIZE = 4096 # Adjust based on memory
TWO_TOWER_TEST_SPLIT = 0.2

# Hybrid Model Parameters
HYBRID_TOP_N_TFIDF = 10
HYBRID_TOP_N_SBERT = 10
HYBRID_TOP_N_TWO_TOWER = 10
HYBRID_FINAL_N = 4
HYBRID_WEIGHT_TFIDF = 0.2
HYBRID_WEIGHT_SBERT = 0.4
HYBRID_WEIGHT_TWO_TOWER = 0.4

print("Config loaded. Course data path:", COURSE_DATA_PATH)

