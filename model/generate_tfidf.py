# generate_tfidf.py
"""Generates TF-IDF vectorizer and matrix from the course data."""

import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import sys
import nltk # Import nltk here for path checks

# --- NLTK Path Setup & Verification ---
# Explicitly define and add a path for NLTK data within the user's home directory
NLTK_DATA_DIR = os.path.join(os.path.expanduser("~"), "nltk_data")
if NLTK_DATA_DIR not in nltk.data.path:
    nltk.data.path.append(NLTK_DATA_DIR)
print(f"[generate_tfidf.py] Ensured NLTK data path includes: {NLTK_DATA_DIR}")
print(f"[generate_tfidf.py] Current NLTK data paths: {nltk.data.path}")
# Ensure the directory exists
os.makedirs(NLTK_DATA_DIR, exist_ok=True)

# --- Add Parent Directory for Package Import ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PARENT_DIR)

# Now import from the package
import config, utils

# Ensure the models directory exists
os.makedirs(config.MODEL_DIR, exist_ok=True)

# Define output paths using the updated config structure
TFIDF_VECTORIZER_OUTPUT_PATH = os.path.join(config.MODEL_DIR, "tfidf_vectorizer.pkl")
TFIDF_MATRIX_OUTPUT_PATH = os.path.join(config.MODEL_DIR, "tfidf_matrix.pkl")

def generate_tfidf_components():
    """Loads data, generates TF-IDF, and saves components."""
    print("Starting TF-IDF generation...")
    
    # 1. Load course data using the updated utils function
    print(f"Loading course data from: {config.COURSE_DATA_PATH}")
    # utils.load_course_data now only keeps specified columns: title, descrition, skills, adjusted_rating, skills_list
    courses_df = utils.load_course_data(config.COURSE_DATA_PATH)
    if courses_df is None or courses_df.empty:
        print("Failed to load course data or required columns missing. Aborting TF-IDF generation.")
        return

    # 2. Prepare text data for TF-IDF using ONLY the selected text columns
    # User specified: Skills, title, descrition
    print("Preparing text data using columns: title, descrition, skills")
    courses_df["tfidf_text"] = (
        courses_df["title"].fillna("") + " " + 
        courses_df["description"].fillna("") + " " + # Use CORRECTED 'descrition'
        courses_df["skills"].apply(lambda x: " ".join(x) if isinstance(x, list) else "").fillna("") # Derived from 'Skills'
    )
    print("Combined text fields for TF-IDF.")

    # 3. Preprocess text using the fallback regex tokenizer from utils
    print("Preprocessing text data (calling utils.preprocess_text_tfidf)...")
    courses_df["processed_text"] = courses_df["tfidf_text"].apply(utils.preprocess_text_tfidf)
    print("Text preprocessing complete.")

    # 4. Initialize and fit TF-IDF Vectorizer
    print("Initializing and fitting TfidfVectorizer...")
    vectorizer = TfidfVectorizer(
        stop_words="english", 
        max_df=0.8,
        min_df=3,
        ngram_range=(1, 2),
        max_features=5000
    )
    # Filter out rows where preprocessing might have failed (unlikely with regex but good practice)
    valid_processed_texts = courses_df.loc[courses_df["processed_text"] != "", "processed_text"]
    if valid_processed_texts.empty:
        print("Error: No valid processed text available for TF-IDF fitting. Aborting.")
        return
        
    tfidf_matrix = vectorizer.fit_transform(valid_processed_texts)
    print(f"TF-IDF matrix generated. Shape: {tfidf_matrix.shape} (based on {len(valid_processed_texts)} valid texts)")
    print(f"Vectorizer vocabulary size: {len(vectorizer.vocabulary_)}")

    # 5. Save the vectorizer and matrix
    print(f"Saving TF-IDF vectorizer to: {TFIDF_VECTORIZER_OUTPUT_PATH}")
    with open(TFIDF_VECTORIZER_OUTPUT_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    print("Vectorizer saved.")

    print(f"Saving TF-IDF matrix to: {TFIDF_MATRIX_OUTPUT_PATH}")
    with open(TFIDF_MATRIX_OUTPUT_PATH, "wb") as f:
        pickle.dump(tfidf_matrix, f)
    print("Matrix saved.")

    # Save course IDs for mapping
    TFIDF_COURSE_IDS_OUTPUT_PATH = os.path.join(config.MODEL_DIR, "tfidf_course_ids.pkl")
    print(f"Saving course IDs to: {TFIDF_COURSE_IDS_OUTPUT_PATH}")
    tfidf_course_ids = courses_df.index.tolist()
    with open(TFIDF_COURSE_IDS_OUTPUT_PATH, "wb") as f:
        pickle.dump(tfidf_course_ids, f)
    print("Course IDs saved.")

    # Update config paths (in memory for this run)
    print("Updating config paths for TF-IDF...")
    config.TFIDF_VECTORIZER_PATH = TFIDF_VECTORIZER_OUTPUT_PATH
    config.TFIDF_MATRIX_PATH = TFIDF_MATRIX_OUTPUT_PATH
    print(f"Config in memory updated: Vectorizer={config.TFIDF_VECTORIZER_PATH}, Matrix={config.TFIDF_MATRIX_PATH}")

    print("TF-IDF generation complete.")

if __name__ == "__main__":
    generate_tfidf_components()

