import pandas as pd
import pickle
from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np

# --- Configuration ---
COURSE_DATA_PATH = "cleaned_courses_with_enhanced_skills.csv"  # Contains course metadata
SBERT_EMBEDDINGS_PATH = "course_sbert_embeddings.pkl"
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"

# --- Load SBERT Model (once) ---
print(f"Loading Sentence-BERT model: {SBERT_MODEL_NAME} for recommender component...")
try:
    sbert_model = SentenceTransformer(SBERT_MODEL_NAME)
    print("Sentence-BERT model loaded successfully.")
except Exception as e:
    print(f"Error loading SBERT model: {e}")
    sbert_model = None # Ensure it's defined for checks later

# --- Load Course Data and Embeddings (once) ---
print(f"Loading course data from: {COURSE_DATA_PATH}")
try:
    df_courses = pd.read_csv(COURSE_DATA_PATH)
    if "skills" in df_courses.columns:
        df_courses["skills"] = df_courses["skills"].apply(
            lambda x: eval(x) if isinstance(x, str) and x.startswith("[") else ([] if pd.isna(x) else [x] if isinstance(x, str) else x)
        )
    print(f"Course data loaded. Shape: {df_courses.shape}")
except FileNotFoundError:
    print(f"Error: Course data file not found at {COURSE_DATA_PATH}.")
    df_courses = None
except Exception as e:
    print(f"An error occurred while loading the course data: {e}")
    df_courses = None

print(f"Loading SBERT course embeddings from: {SBERT_EMBEDDINGS_PATH}")
try:
    with open(SBERT_EMBEDDINGS_PATH, "rb") as f:
        course_embeddings_tensor = torch.tensor(pickle.load(f)) # Convert to tensor for util.cos_sim
    print(f"Course SBERT embeddings loaded. Shape: {course_embeddings_tensor.shape}")
except FileNotFoundError:
    print(f"Error: SBERT embeddings file not found at {SBERT_EMBEDDINGS_PATH}.")
    course_embeddings_tensor = None
except Exception as e:
    print(f"An error occurred while loading the SBERT embeddings: {e}")
    course_embeddings_tensor = None

# --- SBERT Recommender Function ---
def get_sbert_recommendations(query_text, top_n=5):
    """
    Recommends courses based on SBERT embedding similarity to the query text.

    Args:
        query_text (str): The user's query.
        top_n (int): The number of recommendations to return.

    Returns:
        pandas.DataFrame: A DataFrame containing the top_n recommended courses 
                          with their SBERT similarity scores, or an empty DataFrame if an error occurs.
    """
    if sbert_model is None or df_courses is None or course_embeddings_tensor is None:
        print("Error: SBERT model, course data, or embeddings not loaded. Cannot generate recommendations.")
        return pd.DataFrame()

    if not query_text or not isinstance(query_text, str):
        print("Error: Query text must be a non-empty string.")
        return pd.DataFrame()

    try:
        # 1. Generate embedding for the query text
        print(f"Generating SBERT embedding for query: '{query_text}'")
        query_embedding = sbert_model.encode(query_text, convert_to_tensor=True)

        # 2. Compute cosine similarity between query embedding and all course embeddings
        print("Calculating cosine similarities...")
        cosine_scores = util.cos_sim(query_embedding, course_embeddings_tensor)[0]

        # 3. Get top_n scores and their indices
        top_results = torch.topk(cosine_scores, k=min(top_n, len(cosine_scores)))
        
        top_indices = top_results.indices.tolist()
        top_scores = top_results.values.tolist()

        # 4. Retrieve course details for the top indices
        recommendations_df = df_courses.iloc[top_indices].copy()
        recommendations_df["sbert_similarity_score"] = top_scores
        
        # Select and order columns for output
        output_columns = ["title", "provider", "url", "level", "skills", "adjusted_rating", "duration", "sbert_similarity_score"]
        # Ensure all output columns exist, add if not
        for col in output_columns:
            if col not in recommendations_df.columns:
                recommendations_df[col] = np.nan
        
        # Sort by SBERT similarity score
        recommendations_df = recommendations_df.sort_values(by="sbert_similarity_score", ascending=False)
        
        return recommendations_df[output_columns]

    except Exception as e:
        print(f"An error occurred during SBERT recommendation generation: {e}")
        return pd.DataFrame()

# --- Example Usage (for testing this component directly) ---
if __name__ == "__main__":
    print("\n--- Testing SBERT Recommender Component ---")
    
    if sbert_model and df_courses is not None and course_embeddings_tensor is not None:
        test_query = "beginner friendly python course for data analysis"
        print(f"\nTest Query: '{test_query}'")
        recommendations = get_sbert_recommendations(test_query, top_n=3)
        if not recommendations.empty:
            print("\nRecommended Courses (SBERT-based):")
            print(recommendations)
        else:
            print("No recommendations generated for the test query.")
            
        test_query_2 = "advanced machine learning with tensorflow"
        print(f"\nTest Query 2: '{test_query_2}'")
        recommendations_2 = get_sbert_recommendations(test_query_2, top_n=3)
        if not recommendations_2.empty:
            print("\nRecommended Courses (SBERT-based) for Query 2:")
            print(recommendations_2)
        else:
            print("No recommendations generated for test query 2.")
    else:
        print("Skipping direct test as one or more components (model, data, embeddings) failed to load.")

    print("\nSBERT recommender component script finished.")

