import pandas as pd
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity
import torch
import tensorflow as tf
from sentence_transformers import SentenceTransformer, util

# --- Import components from other scripts ---
# NOTE: We are removing the direct import of get_sbert_recommendations from the component
# because we are re-implementing it here with the correct logic.
from sbert_recommender_component import sbert_model as loaded_sbert_model, course_embeddings_tensor as loaded_sbert_course_embeddings
from adapted_two_tower_model import CourseRecommender

# --- Configuration ---
COURSE_DATA_PATH = "data/final(final).csv"
SBERT_COURSE_EMBEDDINGS_FOR_TT_PATH = "models/course_sbert_embeddings.pkl"
TWO_TOWER_MODEL_PATH = 'two_tower_real_interactions.weights.h5'

# --- Global Variables / Load Models ---
print("Loading main course data...")
try:
    df_all_courses = pd.read_csv(COURSE_DATA_PATH)
    if "skills" in df_all_courses.columns:
        df_all_courses["skills_list"] = df_all_courses["skills"].apply(
            lambda x: [s.strip().strip("'") for s in str(x).split(',')] if pd.notna(x) else []
        )
    else:
        df_all_courses["skills_list"] = pd.Series([[] for _ in range(len(df_all_courses))])
    print(f"Main course data loaded. Shape: {df_all_courses.shape}")

    # --- Analysis for User Question on Data Distribution ---
    if 'provider' in df_all_courses.columns:
        print("\n--- Course Provider Distribution Analysis ---")
        print("This shows how many courses are available from each provider in your dataset.")
        print(df_all_courses['provider'].value_counts())
        print("-------------------------------------------\n")
    # --- End Analysis ---
        
except Exception as e:
    print(f"FATAL: Could not load main course data from {COURSE_DATA_PATH}: {e}")
    df_all_courses = None

print("\nLoading SBERT embeddings for Two-Tower model...")
try:
    with open(SBERT_COURSE_EMBEDDINGS_FOR_TT_PATH, "rb") as f:
        all_item_sbert_embeddings = pickle.load(f)
    all_item_sbert_embeddings_tensor_for_tt = tf.convert_to_tensor(all_item_sbert_embeddings, dtype=tf.float32)
    print("SBERT embeddings loaded successfully.")
except Exception as e:
    print(f"FATAL: Could not load SBERT embeddings from {SBERT_COURSE_EMBEDDINGS_FOR_TT_PATH}: {e}")
    all_item_sbert_embeddings_tensor_for_tt = None

# --- Initialize SBERT model for query encoding ---
sbert_model_for_query = SentenceTransformer('all-MiniLM-L6-v2')

# --- DEPRECATED: The CourseRecommender and the trained Two-Tower model are no longer used. ---
# The new strategy relies on session-based semantic search enhancement, which does not require a trained model.
# print("\nInitializing the main Course Recommender...")
# if df_all_courses is not None and all_item_sbert_embeddings_tensor_for_tt is not None:
#     # This single recommender instance will be used for all recommendations.
#     main_recommender = CourseRecommender(
#         courses_df=df_all_courses,
#         course_sbert_embeddings=all_item_sbert_embeddings_tensor_for_tt,
#         model_path=TWO_TOWER_MODEL_PATH
#     )
#     if main_recommender.item_embeddings_norm is None:
#         print("WARNING: Model weights could not be loaded. Personalization will not work.")
# else:
#     main_recommender = None
#     print("WARNING: Recommender could not be initialized due to missing data or embeddings.")

def get_sbert_recommendations(query_text, candidate_df, top_k=10):
    """
    Performs SBERT semantic search on a pre-filtered DataFrame of candidate courses.
    This is the corrected logic: Filter FIRST, then search.
    """
    if loaded_sbert_model is None or loaded_sbert_course_embeddings is None:
        print("SBERT model or embeddings not loaded. Cannot perform search.")
        return pd.DataFrame()

    if candidate_df.empty:
        return pd.DataFrame()

    # Encode the user's query
    query_embedding = loaded_sbert_model.encode(query_text, convert_to_tensor=True)

    # Get the embeddings ONLY for the candidate courses
    candidate_indices = candidate_df.index.tolist()
    candidate_embeddings = torch.index_select(loaded_sbert_course_embeddings, 0, torch.tensor(candidate_indices, dtype=torch.long))

    # Compute cosine similarity between the query and candidate courses
    cosine_scores = util.cos_sim(query_embedding, candidate_embeddings)[0]

    # Get top-k scores and their *indices within the candidate set*
    top_results = torch.topk(cosine_scores, k=min(top_k, len(candidate_df)))
    
    # Map these candidate-specific indices back to the original DataFrame indices
    original_df_indices = [candidate_indices[i] for i in top_results.indices]
    
    # Create recommendations DataFrame
    recommendations = df_all_courses.loc[original_df_indices].copy()
    recommendations['similarity_score'] = top_results.values.numpy()
    
    return recommendations.sort_values(by='similarity_score', ascending=False)

def filter_courses(df, level=None, providers=None, skills=None):
    """Basic filtering for courses."""
    if df is None: return pd.DataFrame()
    filtered_df = df.copy()
    if level and level.lower() != "all levels":
        filtered_df = filtered_df[filtered_df["level"].str.contains(level, case=False, na=False)]
    if providers and isinstance(providers, list) and len(providers) > 0:
        filtered_df = filtered_df[filtered_df["provider"].isin(providers)]
    if skills and isinstance(skills, list) and len(skills) > 0:
        skills_lower = [s.lower().strip() for s in skills]
        def has_required_skills(course_skills):
            if not isinstance(course_skills, list): return False
            course_skills_lower = [s.lower().strip() for s in course_skills]
            return any(req_skill in course_skills_lower for req_skill in skills_lower)
        filtered_df = filtered_df[filtered_df["skills_list"].apply(has_required_skills)]
    return filtered_df

# --- DEPRECATED/REMOVED THE OLD HYBRID AND ADVANCED FUNCTIONS ---
# All logic is now consolidated into a single, cleaner function.

def get_recommendations(
    query_text=None, level=None, skills=None,
    providers=None, top_n=10, user_history=None
):
    """
    Main recommendation function using an intelligent semantic search strategy.
    It completely ignores the `fake_interactions.csv` and the trained Two-Tower model.

    - Filters courses based on structured criteria.
    - If user_history is provided, it combines the titles of those courses with the
      current query_text to create a new, richer query for semantic search.
    - If history is empty, it uses the original query_text.
    """
    if df_all_courses is None:
        print("Recommender not initialized. Cannot provide recommendations.")
        return pd.DataFrame()

    # 1. Start with filtering
    candidate_df = filter_courses(df_all_courses, level, providers, skills)
    if candidate_df.empty:
        return pd.DataFrame()

    final_query = query_text if query_text else ""

    # 2. Enhance the query using the user's history
    if user_history:
        print(f"--- Enhancing search with {len(user_history)} items from session history. ---")
        history_titles = []
        for item_id in user_history:
            # Find the title corresponding to the item_id
            title = df_all_courses[df_all_courses['item_id'] == item_id]['title'].iloc[0]
            if title:
                history_titles.append(title)
        
        if history_titles:
            history_query_part = " ".join(history_titles)
            final_query = f"{final_query} {history_query_part}"
            print(f"--- Combined Query: '{final_query}' ---")

    # 3. Perform semantic search if we have a query to work with
    if final_query.strip():
        recommendations = get_sbert_recommendations(final_query, candidate_df, top_k=top_n)
    # 4. Fallback to top-rated if no query and no history
    else:
        print("--- Strategy: Fallback to Top-Rated (No query or history) ---")
        recommendations = candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

    # Ensure item_id is in the output for the GUI
    if 'item_id' not in recommendations.columns and not recommendations.empty:
        recommendations = recommendations.merge(df_all_courses[['item_id']], left_index=True, right_index=True)

    return recommendations

# This function is what the GUI now calls. It's a simple wrapper.
# --- DEPRECATED ---
# This wrapper is no longer necessary. The GUI will be updated to call get_recommendations directly.
def get_hybrid_recommendations_advanced(*args, **kwargs):
     print("WARNING: get_hybrid_recommendations_advanced is deprecated. Call get_recommendations instead.")
     return get_recommendations(*args, **kwargs)

# --- Example Usage ---
if __name__ == "__main__":
    print("\n--- Testing Simplified Recommender Interface ---")
    if df_all_courses is None:
        print("Cannot run tests as main course data failed to load.")
    else:
        test_query = "learn machine learning with python"
        test_history = ['COURSE-165843-1111-FZ-PP', 'COURSE-269989-1224-FZ-PP'] # Example history

        print(f"\n--- Test 1: Query-based search ---")
        print(get_recommendations(query_text=test_query, top_n=3))

        print(f"\n--- Test 2: History-based search ---")
        print(get_recommendations(user_history=test_history, top_n=3))
        
        print(f"\n--- Test 3: History and Query (History should take precedence) ---")
        print(get_recommendations(query_text="unrelated topic like cooking", user_history=test_history, top_n=3))

        print(f"\n--- Test 4: Structured filters only ---")
        print(get_recommendations(level="Beginner", skills=['python'], top_n=3))

    print("\nRecommender interface script finished.")
