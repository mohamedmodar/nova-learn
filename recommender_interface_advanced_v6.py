import pandas as pd
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import re
import torch # For Two-Tower model

# --- Import components from other scripts ---
from sbert_recommender_component import get_sbert_recommendations, sbert_model as loaded_sbert_model, course_embeddings_tensor as loaded_sbert_course_embeddings, df_courses as sbert_df_courses
from adapted_two_tower_model import TwoTowerModel, UserTower as UserQueryTower, ItemTower
from adapted_two_tower_model import CourseRecommender

# --- Configuration ---
TFIDF_VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"
TFIDF_MATRIX_PATH = "models/tfidf_matrix.pkl"
COURSE_DATA_PATH = "data/final(ready for model).csv"
SBERT_COURSE_EMBEDDINGS_FOR_TT_PATH = "models/course_sbert_embeddings.pkl"

# --- Global Variables / Load Models ---
print("Loading TF-IDF components...")
try:
    with open(TFIDF_VECTORIZER_PATH, "rb") as f:
        tfidf_vectorizer = pickle.load(f)
    with open(TFIDF_MATRIX_PATH, "rb") as f:
        tfidf_matrix = pickle.load(f)
    print("TF-IDF vectorizer and matrix loaded.")
except Exception as e:
    print(f"Error loading TF-IDF components: {e}")
    tfidf_vectorizer = None
    tfidf_matrix = None

print(f"Loading main course data from: {COURSE_DATA_PATH}")
try:
    df_all_courses = pd.read_csv(COURSE_DATA_PATH)
    if "skills_list" in df_all_courses.columns:
        df_all_courses["skills_list"] = df_all_courses["skills_list"].apply(
            lambda x: eval(x) if isinstance(x, str) and x.startswith("[") else ([] if pd.isna(x) else [x] if isinstance(x, str) else x)
        )
    else:
        df_all_courses["skills_list"] = pd.Series([[] for _ in range(len(df_all_courses))])
    print(f"Main course data loaded. Shape: {df_all_courses.shape}")
except Exception as e:
    print(f"Error loading main course data: {e}")
    df_all_courses = None

# --- Initialize NLTK resources ---
try:
    nltk.data.find("corpora/stopwords")
except nltk.downloader.DownloadError:
    nltk.download("stopwords", quiet=True)
stemmer = PorterStemmer()
stop_words = set(stopwords.words("english"))

def preprocess_text_for_tfidf(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"\W", " ", text.lower())
    tokens = text.split()
    stemmed_tokens = [stemmer.stem(word) for word in tokens if word not in stop_words]
    return " ".join(stemmed_tokens)

# --- Two-Tower Model Instantiation ---
print("\nInstantiating Two-Tower Model (conceptual, not trained)...")
TWO_TOWER_SHARED_EMBEDDING_DIM = 128
two_tower_model_instance = None
tt_sbert_model_for_query = None
all_item_sbert_embeddings_tensor_for_tt = None
try:
    sbert_embedding_dim = loaded_sbert_course_embeddings.shape[1] if loaded_sbert_course_embeddings is not None else 384
    two_tower_model_instance = TwoTowerModel(
        query_input_dim=sbert_embedding_dim, 
        item_input_dim=sbert_embedding_dim, 
        shared_embedding_dim=TWO_TOWER_SHARED_EMBEDDING_DIM
    )
    tt_sbert_model_for_query = loaded_sbert_model
    all_item_sbert_embeddings_tensor_for_tt = loaded_sbert_course_embeddings
    print("Two-Tower model and SBERT components for it instantiated.")
except Exception as e:
    print(f"Error instantiating Two-Tower model or its SBERT components: {e}")

# --- Helper: Filter courses ---
def filter_courses(df, level=None, providers=None, skills=None, duration_pref=None):
    if df is None: return pd.DataFrame()
    filtered_df = df.copy()
    if level and level.lower() != "all levels":
        filtered_df = filtered_df[filtered_df["level"].str.contains(level, case=False, na=False)]
    if providers: filtered_df = filtered_df[filtered_df["provider"].isin(providers)]
    if skills:
        skills_lower = [s.lower() for s in skills]
        filtered_df = filtered_df[filtered_df["skills_list"].apply(lambda x: all(s_query in [s_item.lower() for s_item in x] for s_query in skills_lower) if isinstance(x, list) else False)]
    if duration_pref:
        filtered_df["duration"] = pd.to_numeric(filtered_df["duration"], errors="coerce")
        if duration_pref == "short": filtered_df = filtered_df[filtered_df["duration"] <= 10]
        elif duration_pref == "medium": filtered_df = filtered_df[(filtered_df["duration"] > 10) & (filtered_df["duration"] <= 50)]
        elif duration_pref == "long": filtered_df = filtered_df[filtered_df["duration"] > 50]
    return filtered_df

# --- Model-Specific Recommendation Functions ---
def _get_tfidf_recs(candidate_df, content_query, top_n):
    if not content_query or tfidf_vectorizer is None or tfidf_matrix is None:
        print("TF-IDF: Missing query or components. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    processed_query = preprocess_text_for_tfidf(content_query)
    query_vector = tfidf_vectorizer.transform([processed_query])
    valid_indices = [idx for idx in candidate_df.index if idx < tfidf_matrix.shape[0]]
    if not valid_indices:
        print("TF-IDF: No valid indices. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    candidate_tfidf_matrix = tfidf_matrix[valid_indices]
    cosine_similarities = cosine_similarity(query_vector, candidate_tfidf_matrix).flatten()
    score_df = pd.DataFrame({"content_score": cosine_similarities}, index=candidate_df.loc[valid_indices].index)
    candidate_df_with_scores = candidate_df.join(score_df)
    candidate_df_with_scores["content_score"] = candidate_df_with_scores["content_score"].fillna(0)
    return candidate_df_with_scores.sort_values(by=["content_score", "adjusted_rating"], ascending=[False, False]).head(top_n)

def _get_sbert_recs(candidate_df, content_query, top_n):
    if not content_query or loaded_sbert_model is None or loaded_sbert_course_embeddings is None or sbert_df_courses is None:
        print("SBERT: Missing query or components. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    sbert_recs_unfiltered = get_sbert_recommendations(content_query, top_n=len(df_all_courses))
    if sbert_recs_unfiltered.empty:
        print("SBERT: Unfiltered SBERT recommendations empty. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    sbert_recs_filtered = sbert_recs_unfiltered[sbert_recs_unfiltered.index.isin(candidate_df.index)]
    if sbert_recs_filtered.empty:
        print("SBERT: No SBERT recs in filtered candidates. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    return sbert_recs_filtered.sort_values(by=["sbert_similarity_score", "adjusted_rating"], ascending=[False, False]).head(top_n)

def _get_two_tower_recs_placeholder(candidate_df, content_query, top_n):
    print("Two-Tower (Placeholder) selected.")
    if not content_query or two_tower_model_instance is None or tt_sbert_model_for_query is None or all_item_sbert_embeddings_tensor_for_tt is None:
        print("Two-Tower: Missing query or components. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    try:
        # Fallback to SBERT as TT is not trained
        sbert_recs = _get_sbert_recs(candidate_df, content_query, top_n)
        if not sbert_recs.empty:
            sbert_recs["content_score_model"] = "TwoTower (SBERT Fallback)"
        return sbert_recs
    except Exception as e:
        print(f"Error in Two-Tower placeholder: {e}. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

def _get_two_tower_recs_trained(candidate_df, content_query, top_n):
    print("Two-Tower (Trained) selected.")
    try:
        recommender = CourseRecommender(model_path='two_tower.weights.h5')
        recs = recommender.recommend(query_text=content_query, top_k=top_n)
        # Filter to candidate_df indices if possible
        if not recs.empty:
            recs = recs[recs.index.isin(candidate_df.index)]
        return recs.head(top_n)
    except Exception as e:
        print(f"Error in Two-Tower trained: {e}. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

def _get_hybrid_tfidf_sbert_recs(candidate_df, content_query, top_n):
    sbert_primary_recs = pd.DataFrame()
    if content_query and loaded_sbert_model:
        sbert_recs_unfiltered = get_sbert_recommendations(content_query, top_n=len(df_all_courses))
        if not sbert_recs_unfiltered.empty:
            sbert_primary_recs = sbert_recs_unfiltered[sbert_recs_unfiltered.index.isin(candidate_df.index)].copy()
    
    if not sbert_primary_recs.empty:
        if tfidf_vectorizer and content_query:
            processed_query_tfidf = preprocess_text_for_tfidf(content_query)
            query_vector_tfidf = tfidf_vectorizer.transform([processed_query_tfidf])
            valid_indices = [idx for idx in sbert_primary_recs.index if idx < tfidf_matrix.shape[0]]
            if valid_indices:
                candidate_tfidf_matrix = tfidf_matrix[valid_indices]
                cosine_similarities = cosine_similarity(query_vector_tfidf, candidate_tfidf_matrix).flatten()
                tfidf_scores_series = pd.Series(cosine_similarities, index=sbert_primary_recs.loc[valid_indices].index)
                sbert_primary_recs["tfidf_score"] = tfidf_scores_series
            sbert_primary_recs["tfidf_score"] = sbert_primary_recs.get("tfidf_score", 0.0).fillna(0.0)
            return sbert_primary_recs.sort_values(by=["sbert_similarity_score", "tfidf_score", "adjusted_rating"], ascending=[False, False, False]).head(top_n)
        else: # Only SBERT scores
            return sbert_primary_recs.sort_values(by=["sbert_similarity_score", "adjusted_rating"], ascending=[False, False]).head(top_n)
    else: # SBERT failed, try full TF-IDF
        print("Hybrid: SBERT failed. Trying TF-IDF.")
        return _get_tfidf_recs(candidate_df, content_query, top_n)

# --- Main Recommendation Function (Refactored) ---
def get_hybrid_recommendations_advanced(
    query_text=None, topic=None, level=None, skills=None, 
    duration_pref=None, providers=None, top_n=5, 
    model_type="hybrid_tfidf_sbert"
):
    if df_all_courses is None: return pd.DataFrame()
    candidate_df = filter_courses(df_all_courses, level, providers, skills, duration_pref)
    if candidate_df.empty: return pd.DataFrame()
    content_query = query_text if query_text else topic
    recommendations = pd.DataFrame()

    if model_type == "tfidf":
        recommendations = _get_tfidf_recs(candidate_df, content_query, top_n)
    elif model_type == "sbert":
        recommendations = _get_sbert_recs(candidate_df, content_query, top_n)
    elif model_type == "two_tower":
        recommendations = _get_two_tower_recs_trained(candidate_df, content_query, top_n)
    elif model_type == "two_tower_placeholder":
        recommendations = _get_two_tower_recs_placeholder(candidate_df, content_query, top_n)
    elif model_type == "hybrid_tfidf_sbert":
        recommendations = _get_hybrid_tfidf_sbert_recs(candidate_df, content_query, top_n)
    else:
        print(f"Unknown model_type \t'{model_type}\t'. Defaulting to rating-based ranking.")
        recommendations = candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

    if recommendations.empty:
        print("No recommendations generated by selected model. Defaulting to rating-based.")
        recommendations = candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

    if not recommendations.empty:
        output_cols = ["title", "provider", "url", "level", "skills_list", "adjusted_rating", "duration"]
        for col_name in ["content_score", "sbert_similarity_score", "tfidf_score", "content_score_model", "similarity_score", "two_tower_similarity_score"]:
            if col_name in recommendations.columns: output_cols.append(col_name)
        final_df = pd.DataFrame()
        for col in output_cols:
            if col in recommendations.columns: final_df[col] = recommendations[col]
            else: final_df[col] = np.nan 
        return final_df.head(top_n)
    return pd.DataFrame()

# --- Example Usage ---
if __name__ == "__main__":
    print("\n--- Testing Advanced Recommender Interface ---")
    if df_all_courses is None:
        print("Cannot run tests as main course data failed to load.")
    else:
        test_query = "learn machine learning with python"
        structured_input = {"topic": "data science", "level": "Beginner", "skills": ["python"], "duration_pref": "short"}
        
        print(f"\n--- Test TF-IDF: 	'{test_query}	' ---")
        print(get_hybrid_recommendations_advanced(query_text=test_query, model_type="tfidf"))
        
        print(f"\n--- Test SBERT: 	'{test_query}	' ---")
        print(get_hybrid_recommendations_advanced(query_text=test_query, model_type="sbert"))

        print(f"\n--- Test Hybrid TF-IDF/SBERT: 	'{test_query}	' ---")
        print(get_hybrid_recommendations_advanced(query_text=test_query, model_type="hybrid_tfidf_sbert"))

        print(f"\n--- Test Two-Tower (Placeholder): 	'{test_query}	' ---")
        print(get_hybrid_recommendations_advanced(query_text=test_query, model_type="two_tower_placeholder"))

        print(f"\n--- Test SBERT with structured: {structured_input} ---")
        print(get_hybrid_recommendations_advanced(**structured_input, model_type="sbert"))

        print(f"\n--- Test Unknown Model Type: 	'{test_query}	' ---")
        print(get_hybrid_recommendations_advanced(query_text=test_query, model_type="unknown_test"))

    print("\nAdvanced recommender interface script finished.")

