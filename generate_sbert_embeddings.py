# generate_sbert_embeddings.py
"""Generates SBERT embeddings for course content."""

import pandas as pd
import pickle
from sentence_transformers import SentenceTransformer
import os
import sys
import torch # Import torch to check for GPU availability

# --- Add Parent Directory for Package Import ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# Now import from the package
import config, utils

# Ensure the models directory exists
os.makedirs(config.MODEL_DIR, exist_ok=True)

# Define output paths using the updated config structure
SBERT_EMBEDDINGS_OUTPUT_PATH = os.path.join(config.MODEL_DIR, "course_sbert_embeddings.pkl")
SBERT_COURSE_IDS_OUTPUT_PATH = os.path.join(config.MODEL_DIR, "sbert_course_ids.pkl")

def generate_embeddings():
    """Loads data, generates SBERT embeddings, and saves them."""
    print("Starting SBERT embedding generation...")
    
    # 1. Load course data using the updated utils function
    print(f"Loading course data from: {config.COURSE_DATA_PATH}")
    # utils.load_course_data now only keeps specified columns: title, description, skills, adjusted_rating, skills_list
    courses_df = utils.load_course_data(config.COURSE_DATA_PATH)
    if courses_df is None or courses_df.empty:
        print("Failed to load course data or required columns missing. Aborting SBERT generation.")
        return

    # 2. Prepare text data for SBERT using ONLY the selected text columns
    # User specified: Skills, title, description
    print("Preparing text data using columns: title, description, skills_list") # Changed 'skills' to 'skills_list'
    courses_df["processed_text"] = (
        courses_df["title"].fillna("") + ". " + # Add separator
        courses_df["description"].fillna("") + ". " + # Use CORRECTED name 'description', add separator
        courses_df["skills_list"].apply(lambda x: " ".join(x) if isinstance(x, list) else "").fillna("") # Use 'skills_list'
    )
    # Handle potential empty strings after concatenation
    courses_df["processed_text"] = courses_df["processed_text"].apply(lambda x: x.strip() if x.strip() else "No content")
    print("Combined text fields for SBERT.")

    # 3. Initialize SBERT model
    print(f"Initializing SBERT model: {config.SBERT_MODEL_NAME}")
    # Check for GPU availability
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    try:
        model = SentenceTransformer(config.SBERT_MODEL_NAME, device=device)
    except Exception as e:
        print(f"Error initializing SentenceTransformer model: {e}")
        print("Attempting to load model on CPU explicitly.")
        try:
            model = SentenceTransformer(config.SBERT_MODEL_NAME, device="cpu")
            print("Successfully loaded model on CPU.")
        except Exception as e_cpu:
            print(f"Failed to load model on CPU as well: {e_cpu}. Aborting.")
            return
            
    print("SBERT model initialized.")

    # 4. Generate embeddings
    print("Generating embeddings (this may take some time)...")
    course_texts = courses_df["processed_text"].tolist()
    
    # Define batch size based on device
    batch_size = 64 if device == "cuda" else 32 # Smaller batch size for CPU
    print(f"Using batch size: {batch_size}")
    
    embeddings = model.encode(course_texts, show_progress_bar=True, batch_size=batch_size)
    print(f"Embeddings generated. Shape: {embeddings.shape}")

    # 5. Save the embeddings
    print(f"Saving SBERT embeddings to: {SBERT_EMBEDDINGS_OUTPUT_PATH}")
    with open(SBERT_EMBEDDINGS_OUTPUT_PATH, "wb") as f:
        pickle.dump(embeddings, f)
    print("Embeddings saved.")

    # Save course IDs for mapping (CRITICAL FIX HERE)
    print(f"Saving course IDs to: {SBERT_COURSE_IDS_OUTPUT_PATH}")
    with open(SBERT_COURSE_IDS_OUTPUT_PATH, "wb") as f:
        pickle.dump(courses_df['item_id'].tolist(), f) # <--- FIXED: Save actual item_ids, not index
    print("Course IDs saved.")

    # Update config paths (in memory for this run)
    print("Updating config paths for SBERT...")
    config.SBERT_EMBEDDINGS_PATH = SBERT_EMBEDDINGS_OUTPUT_PATH
    config.SBERT_COURSE_IDS_PATH = SBERT_COURSE_IDS_OUTPUT_PATH
    print(f"Config in memory updated: Embeddings={config.SBERT_EMBEDDINGS_PATH}, Course IDs={config.SBERT_COURSE_IDS_PATH}")

    print("SBERT embedding generation complete.")

if __name__ == "__main__":
    generate_embeddings()
