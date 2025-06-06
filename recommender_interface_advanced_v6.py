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
import tensorflow as tf

# --- Import components from other scripts ---
from sbert_recommender_component import get_sbert_recommendations, sbert_model as loaded_sbert_model, course_embeddings_tensor as loaded_sbert_course_embeddings, df_courses as sbert_df_courses
from adapted_two_tower_model import TwoTowerModel, UserTower as UserQueryTower, ItemTower
from adapted_two_tower_model import CourseRecommender

# --- Configuration ---
TFIDF_VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"
TFIDF_MATRIX_PATH = "models/tfidf_matrix.pkl"
COURSE_DATA_PATH = "data/final(final).csv"
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
    # Print sample of skills to see their format
    print("\nSample of skills from dataset:")
    for i in range(min(5, len(df_all_courses))):
        print(f"Row {i} skills: {df_all_courses['skills'].iloc[i]}")
    
    # Process skills column - handle the format where skills are comma-separated strings
    if "skills" in df_all_courses.columns:
        df_all_courses["skills_list"] = df_all_courses["skills"].apply(
            lambda x: [s.strip().strip("'") for s in str(x).split(',')] if pd.notna(x) else []
        )
        # Print sample of processed skills
        print("\nSample of processed skills_list:")
        for i in range(min(5, len(df_all_courses))):
            print(f"Row {i} processed skills: {df_all_courses['skills_list'].iloc[i]}")
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
    two_tower_model_instance = TwoTowerModel(vector_dim=sbert_embedding_dim)
    tt_sbert_model_for_query = loaded_sbert_model
    all_item_sbert_embeddings_tensor_for_tt = loaded_sbert_course_embeddings
    print("Two-Tower model and SBERT components for it instantiated.")
except Exception as e:
    print(f"Error instantiating Two-Tower model or its SBERT components: {e}")

# --- Helper: Filter courses ---
def filter_courses(df, level=None, providers=None, skills=None, duration_pref=None):
    if df is None: return pd.DataFrame()
    filtered_df = df.copy()
    
    # Filter by level
    if level and level.lower() != "all levels":
        filtered_df = filtered_df[filtered_df["level"].str.contains(level, case=False, na=False)]
    
    # Filter by provider
    if providers and isinstance(providers, list) and len(providers) > 0:
        filtered_df = filtered_df[filtered_df["provider"].isin(providers)]
    
    # Filter by skills - improved logic for comma-separated skills
    if skills and isinstance(skills, list) and len(skills) > 0:
        print(f"\nFiltering by skills: {skills}")
        skills_lower = [s.lower().strip() for s in skills]
        print(f"Normalized skills to search for: {skills_lower}")
        
        def has_required_skills(course_skills):
            if not isinstance(course_skills, list):
                print(f"Warning: course_skills is not a list: {type(course_skills)}")
                return False
            # Convert all skills to lowercase and strip whitespace for comparison
            course_skills_lower = [s.lower().strip() for s in course_skills]
            # Check if any of the required skills are in the course skills
            matches = any(req_skill in course_skills_lower for req_skill in skills_lower)
            if matches:
                print(f"Found matching skills in course: {course_skills_lower}")
            return matches
            
        filtered_df = filtered_df[filtered_df["skills_list"].apply(has_required_skills)]
        print(f"After skills filtering: {len(filtered_df)} courses remaining")
    
    # Filter by duration
    if duration_pref:
        filtered_df["duration"] = pd.to_numeric(filtered_df["duration"], errors="coerce")
        if duration_pref == "short": 
            filtered_df = filtered_df[filtered_df["duration"] <= 10]
        elif duration_pref == "medium": 
            filtered_df = filtered_df[(filtered_df["duration"] > 10) & (filtered_df["duration"] <= 50)]
        elif duration_pref == "long": 
            filtered_df = filtered_df[filtered_df["duration"] > 50]
    
    return filtered_df

# --- Model-Specific Recommendation Functions ---
def _get_tfidf_recs_enhanced(candidate_df, enriched_query_vector, query_text, top_n):
    """Enhanced TF-IDF recommendations using enriched query"""
    if not query_text or tfidf_vectorizer is None or tfidf_matrix is None:
        print("TF-IDF: Missing query or components. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    
    # Use original TF-IDF processing for text query
    processed_query = preprocess_text_for_tfidf(query_text)
    query_vector = tfidf_vectorizer.transform([processed_query])
    valid_indices = [idx for idx in candidate_df.index if idx < tfidf_matrix.shape[0]]
    if not valid_indices:
        print("TF-IDF: No valid indices. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    
    candidate_tfidf_matrix = tfidf_matrix[valid_indices]
    cosine_similarities = cosine_similarity(query_vector, candidate_tfidf_matrix).flatten()
    
    # Enhance scores with user preferences (level, duration matching)
    enhanced_scores = []
    for i, idx in enumerate(valid_indices):
        base_score = cosine_similarities[i]
        course_row = candidate_df.loc[idx]
        
        # Bonus for level matching (if enriched_query_vector contains level info)
        level_bonus = 0
        if len(enriched_query_vector) > 384:  # Has additional features
            level_prefs = enriched_query_vector[384:387]  # Level encoding
            course_level = course_row.get('level', '').lower()
            if course_level == 'beginner' and level_prefs[0] > 0.5:
                level_bonus = 0.1
            elif course_level == 'intermediate' and level_prefs[1] > 0.5:
                level_bonus = 0.1
            elif course_level == 'advanced' and level_prefs[2] > 0.5:
                level_bonus = 0.1
        
        enhanced_score = base_score + level_bonus
        enhanced_scores.append(enhanced_score)
    
    score_df = pd.DataFrame({"tfidf_score": enhanced_scores}, index=candidate_df.loc[valid_indices].index)
    candidate_df_with_scores = candidate_df.join(score_df)
    candidate_df_with_scores["tfidf_score"] = candidate_df_with_scores["tfidf_score"].fillna(0)
    return candidate_df_with_scores.sort_values(by=["tfidf_score", "adjusted_rating"], ascending=[False, False]).head(top_n)

def _get_sbert_recs_enhanced(candidate_df, enriched_query_vector, top_n):
    """Enhanced SBERT recommendations using enriched query vector"""
    if loaded_sbert_model is None or loaded_sbert_course_embeddings is None:
        print("SBERT: Missing components. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    
    try:
        # Use enriched query vector (take first 384 dimensions for SBERT compatibility)
        enriched_query_emb = enriched_query_vector[:384]
        enriched_query_tensor = torch.tensor(enriched_query_emb).unsqueeze(0)
        
        # Compute cosine similarity with course embeddings
        cosine_scores = torch.cosine_similarity(enriched_query_tensor, loaded_sbert_course_embeddings, dim=1)
        
        # Get top scores and indices for candidate courses
        candidate_indices = list(candidate_df.index)
        candidate_scores = cosine_scores[candidate_indices]
        
        # Create results DataFrame
        sbert_recs = candidate_df.copy()
        sbert_recs['sbert_score'] = candidate_scores.numpy()
        
        return sbert_recs.sort_values(by=["sbert_score", "adjusted_rating"], ascending=[False, False]).head(top_n)
        
    except Exception as e:
        print(f"Error in enhanced SBERT recommendations: {e}")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

def _get_two_tower_recs_enhanced(candidate_df, enriched_query_vector, context_vector, top_n):
    """Enhanced Two-Tower recommendations using enriched query and context vectors"""
    print("Two-Tower (Enhanced) selected.")
    try:
        recommender = CourseRecommender(model_path='two_tower.weights.h5')
        
        # Convert numpy arrays to TensorFlow tensors
        query_tensor = tf.convert_to_tensor([enriched_query_vector[:384]], dtype=tf.float32)
        context_tensor = tf.convert_to_tensor([context_vector], dtype=tf.float32)
        
        # Get user embedding using enhanced inputs
        user_embedding = recommender.model.get_user_embedding(query_tensor, context_tensor)
        user_embedding_norm = tf.nn.l2_normalize(user_embedding, axis=-1)
        
        # Get candidate course embeddings
        candidate_indices = list(candidate_df.index)
        candidate_embeddings = tf.gather(recommender.course_embeddings, candidate_indices)
        candidate_item_embeddings = recommender.model.get_item_embedding(candidate_embeddings)
        candidate_item_embeddings_norm = tf.nn.l2_normalize(candidate_item_embeddings, axis=-1)
        
        # Compute similarities
        similarity_scores = tf.matmul(user_embedding_norm, candidate_item_embeddings_norm, transpose_b=True)
        similarity_scores = tf.squeeze(similarity_scores, axis=0)
        
        # Create results DataFrame
        two_tower_recs = candidate_df.copy()
        two_tower_recs['two_tower_score'] = similarity_scores.numpy()
        
        return two_tower_recs.sort_values(by=["two_tower_score", "adjusted_rating"], ascending=[False, False]).head(top_n)
        
    except Exception as e:
        print(f"Error in Two-Tower enhanced: {e}. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

# --- Main Recommendation Function (Enhanced) ---
def get_hybrid_recommendations_advanced(
    query_text=None, topic=None, level=None, skills=None, 
    duration_pref=None, providers=None, top_n=5, 
    model_type="hybrid", enable_diversity=True, enable_fuzzy_skills=True,
    enable_personalization=True
):
    if df_all_courses is None: return pd.DataFrame()
    
    # Analyze user intent
    content_query = query_text if query_text else topic
    intent_features = analyze_query_intent(content_query, skills, level)
    print(f"Detected intent: {intent_features}")
    
    # Use enhanced filtering
    candidate_df = filter_courses_enhanced(
        df_all_courses, level, providers, skills, duration_pref, 
        enable_fuzzy_skills=enable_fuzzy_skills
    )
    if candidate_df.empty: return pd.DataFrame()
    
    # Create enriched vectors
    enriched_query_vector = create_enriched_query_vector(content_query, skills, level, duration_pref)
    context_vector = create_context_vector(skills, level, duration_pref)
    
    recommendations = pd.DataFrame()

    if model_type == "tfidf":
        recommendations = _get_tfidf_recs_enhanced(candidate_df, enriched_query_vector, content_query, top_n)
    elif model_type == "sbert":
        recommendations = _get_sbert_recs_enhanced(candidate_df, enriched_query_vector, top_n)
    elif model_type == "two_tower":
        recommendations = _get_two_tower_recs_enhanced(candidate_df, enriched_query_vector, context_vector, top_n)
    elif model_type == "two_tower_placeholder":
        recommendations = _get_two_tower_recs_placeholder(candidate_df, content_query, top_n)
    elif model_type == "hybrid":
        recommendations = _get_hybrid_enhanced_adaptive(candidate_df, enriched_query_vector, context_vector, content_query, skills, level, duration_pref, top_n)
    else:
        print(f"Unknown model_type '{model_type}'. Defaulting to rating-based ranking.")
        recommendations = candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

    if recommendations.empty:
        print("No recommendations generated by selected model. Defaulting to rating-based.")
        recommendations = candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

    # Apply personalized reranking if enabled
    if enable_personalization and not recommendations.empty:
        recommendations = personalized_reranking(recommendations, content_query, skills, level, intent_features)
        print("Applied personalized reranking based on user intent")

    # Apply diversity if enabled
    if enable_diversity and len(recommendations) > 2:
        recommendations = diversify_recommendations(recommendations)
        print("Applied diversity selection")

    if not recommendations.empty:
        # Define base columns that should always be included
        output_cols = ["title", "provider", "url", "level", "skills_list", "adjusted_rating", "duration", "description"]
        
        # Add similarity score columns if they exist
        score_columns = ["tfidf_score", "sbert_score", "two_tower_score", "combined_score", "difficulty_score"]
        for col in score_columns:
            if col in recommendations.columns:
                output_cols.append(col)
        
        # Create final DataFrame with all available columns
        available_cols = [col for col in output_cols if col in recommendations.columns]
        final_df = recommendations[available_cols].copy()
        
        # Ensure all score columns exist, fill with 0 if missing
        for col in ["tfidf_score", "sbert_score", "two_tower_score", "combined_score"]:
            if col not in final_df.columns:
                final_df[col] = 0
        
        return final_df.head(top_n)
    return pd.DataFrame()

# --- Enhanced Input Encoding Functions ---
def encode_level(level):
    """Encode level as one-hot vector"""
    level_mapping = {
        'beginner': [1, 0, 0],
        'intermediate': [0, 1, 0], 
        'advanced': [0, 0, 1],
        'all levels': [0.33, 0.33, 0.33]  # Equal weight for all levels
    }
    if level and level.lower() in level_mapping:
        return np.array(level_mapping[level.lower()])
    return np.array([0.33, 0.33, 0.33])  # Default equal weight

def encode_duration_preference(duration_pref):
    """Encode duration preference as numerical feature"""
    duration_mapping = {
        'short': 0.2,    # Prefer shorter courses
        'medium': 0.5,   # Neutral
        'long': 0.8,     # Prefer longer courses
        'any': 0.5       # Neutral
    }
    if duration_pref and duration_pref.lower() in duration_mapping:
        return duration_mapping[duration_pref.lower()]
    return 0.5  # Default neutral

def encode_skills_with_sbert(skills_list):
    """Encode skills using SBERT model"""
    if not skills_list or not loaded_sbert_model:
        return np.zeros(384)  # Return zero vector if no skills or model
    
    try:
        # Encode each skill and average the embeddings
        skill_embeddings = []
        for skill in skills_list:
            if skill.strip():  # Only process non-empty skills
                skill_embedding = loaded_sbert_model.encode(skill.strip())
                skill_embeddings.append(skill_embedding)
        
        if skill_embeddings:
            # Average all skill embeddings
            avg_skill_embedding = np.mean(skill_embeddings, axis=0)
            return avg_skill_embedding
        else:
            return np.zeros(384)
    except Exception as e:
        print(f"Error encoding skills: {e}")
        return np.zeros(384)

def create_enriched_query_vector(query_text, skills, level, duration_pref):
    """Create an enriched query vector combining all user inputs"""
    # Get base query embedding
    if query_text and loaded_sbert_model:
        try:
            query_embedding = loaded_sbert_model.encode(query_text)
        except Exception as e:
            print(f"Error encoding query: {e}")
            query_embedding = np.zeros(384)
    else:
        query_embedding = np.zeros(384)
    
    # Get skills embedding
    skills_embedding = encode_skills_with_sbert(skills)
    
    # Get level encoding
    level_encoding = encode_level(level)
    
    # Get duration encoding
    duration_encoding = encode_duration_preference(duration_pref)
    
    # Combine all features with weights
    # Query gets 60% weight, skills get 30%, level gets 7%, duration gets 3%
    enriched_query = (
        0.6 * query_embedding + 
        0.3 * skills_embedding
    )
    
    # Append level and duration as additional features
    enriched_features = np.concatenate([
        enriched_query,
        level_encoding,
        [duration_encoding]
    ])
    
    return enriched_features

def create_context_vector(skills, level, duration_pref):
    """Create a context vector for Two-Tower model"""
    # Get skills embedding
    skills_embedding = encode_skills_with_sbert(skills)
    
    # Get level encoding
    level_encoding = encode_level(level)
    
    # Get duration encoding
    duration_encoding = encode_duration_preference(duration_pref)
    
    # Create context vector (same dimension as SBERT for compatibility)
    # Use skills as base and append other features
    context_base = skills_embedding  # 384 dimensions
    
    # Scale other features to fit in remaining space
    level_scaled = np.tile(level_encoding, 128)[:384-len(level_encoding)-1]  # Scale to fit
    duration_scaled = np.array([duration_encoding])
    
    # Replace last few dimensions with level and duration info
    context_vector = context_base.copy()
    context_vector[-4:-1] = level_encoding
    context_vector[-1] = duration_encoding
    
    return context_vector

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
        print(get_hybrid_recommendations_advanced(query_text=test_query, model_type="hybrid"))

        print(f"\n--- Test Two-Tower (Placeholder): 	'{test_query}	' ---")
        print(get_hybrid_recommendations_advanced(query_text=test_query, model_type="two_tower_placeholder"))

        print(f"\n--- Test SBERT with structured: {structured_input} ---")
        print(get_hybrid_recommendations_advanced(**structured_input, model_type="sbert"))

        print(f"\n--- Test Unknown Model Type: 	'{test_query}	' ---")
        print(get_hybrid_recommendations_advanced(query_text=test_query, model_type="unknown_test"))

    print("\nAdvanced recommender interface script finished.")

def _get_hybrid_enhanced_adaptive(candidate_df, enriched_query_vector, context_vector, content_query, skills, level, duration_pref, top_n):
    """
    Enhanced hybrid recommender with adaptive weighting and diversity.
    """
    # Get adaptive weights based on query characteristics
    adaptive_weights = adaptive_weight_learning(content_query, skills, level, duration_pref)
    
    # Get top 10 results from each enhanced model
    tfidf_recs = _get_tfidf_recs_enhanced(candidate_df, enriched_query_vector, content_query, 10)
    sbert_recs = _get_sbert_recs_enhanced(candidate_df, enriched_query_vector, 10)
    two_tower_recs = _get_two_tower_recs_enhanced(candidate_df, enriched_query_vector, context_vector, 10)

    # Create a union of all recommended course indices
    all_indices = set(tfidf_recs.index) | set(sbert_recs.index) | set(two_tower_recs.index)

    if not all_indices:
        print("Hybrid model: No recommendations found from any individual model.")
        return pd.DataFrame()

    # Create a combined DataFrame with all unique candidates
    combined_recs = candidate_df.loc[list(all_indices)].copy()

    # Join scores from each model
    score_columns = {
        'tfidf_score': tfidf_recs,
        'sbert_score': sbert_recs,
        'two_tower_score': two_tower_recs
    }
    
    for score_col, model_recs in score_columns.items():
        if score_col in model_recs.columns:
            combined_recs = combined_recs.join(model_recs[[score_col]])
    
    # Fill NaN values with 0 for courses not in a model's top 10
    score_cols = ['tfidf_score', 'sbert_score', 'two_tower_score']
    for col in score_cols:
        if col not in combined_recs:
            combined_recs[col] = 0
    combined_recs[score_cols] = combined_recs[score_cols].fillna(0)

    # Normalize scores to a 0-1 scale to ensure fair weighting
    for col in score_cols:
        max_score = combined_recs[col].max()
        if max_score > 0:
            combined_recs[col] = combined_recs[col] / max_score

    # Calculate final hybrid score with adaptive weights
    combined_recs['combined_score'] = (
        adaptive_weights['tfidf'] * combined_recs['tfidf_score'] +
        adaptive_weights['sbert'] * combined_recs['sbert_score'] +
        adaptive_weights['two_tower'] * combined_recs['two_tower_score']
    )

    # Sort by the final combined score and return the top N results
    return combined_recs.sort_values(by='combined_score', ascending=False).head(top_n*2)  # Get more for diversity

# Also need the original functions for backward compatibility
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
    score_df = pd.DataFrame({"tfidf_score": cosine_similarities}, index=candidate_df.loc[valid_indices].index)
    candidate_df_with_scores = candidate_df.join(score_df)
    candidate_df_with_scores["tfidf_score"] = candidate_df_with_scores["tfidf_score"].fillna(0)
    return candidate_df_with_scores.sort_values(by=["tfidf_score", "adjusted_rating"], ascending=[False, False]).head(top_n)

def _get_sbert_recs(candidate_df, content_query, top_n):
    if not content_query or loaded_sbert_model is None or loaded_sbert_course_embeddings is None or sbert_df_courses is None:
        print("SBERT: Missing query or components. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    sbert_recs_unfiltered = get_sbert_recommendations(content_query, top_n=len(df_all_courses))
    if sbert_recs_unfiltered.empty:
        print("SBERT: Unfiltered SBERT recommendations empty. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    
    # Get the full course information for the recommended courses
    sbert_recs_filtered = candidate_df.loc[sbert_recs_unfiltered.index].copy()
    sbert_recs_filtered['sbert_score'] = sbert_recs_unfiltered['sbert_similarity_score']
    
    if sbert_recs_filtered.empty:
        print("SBERT: No SBERT recs in filtered candidates. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    return sbert_recs_filtered.sort_values(by=["sbert_score", "adjusted_rating"], ascending=[False, False]).head(top_n)

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
            # Get the full course information for the recommended courses
            two_tower_recs = candidate_df.loc[recs.index].copy()
            if 'similarity_score' in recs.columns:
                two_tower_recs['two_tower_score'] = recs['similarity_score']
            return two_tower_recs.head(top_n)
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)
    except Exception as e:
        print(f"Error in Two-Tower trained: {e}. Ranking by adjusted_rating.")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

def _get_hybrid_tfidf_sbert_recs(candidate_df, content_query, top_n):
    """
    A more robust hybrid recommender.
    1. Gathers top 10 from TF-IDF, SBERT, and Two-Tower.
    2. Creates a union of all candidates.
    3. Calculates a normalized, weighted score for each candidate.
    4. Returns the top N ranked results.
    """
    # Get top 10 results from each model
    tfidf_recs = _get_tfidf_recs(candidate_df, content_query, 10)
    sbert_recs = _get_sbert_recs(candidate_df, content_query, 10)
    two_tower_recs = _get_two_tower_recs_trained(candidate_df, content_query, 10)

    # Create a union of all recommended course indices
    all_indices = set(tfidf_recs.index) | set(sbert_recs.index) | set(two_tower_recs.index)

    if not all_indices:
        print("Hybrid model: No recommendations found from any individual model.")
        return pd.DataFrame()

    # Create a combined DataFrame with all unique candidates
    combined_recs = candidate_df.loc[list(all_indices)].copy()

    # Join scores from each model
    score_columns = {
        'tfidf_score': tfidf_recs,
        'sbert_score': sbert_recs,
        'two_tower_score': two_tower_recs
    }
    
    for score_col, model_recs in score_columns.items():
        if score_col in model_recs.columns:
            combined_recs = combined_recs.join(model_recs[[score_col]])
    
    # Fill NaN values with 0 for courses not in a model's top 10
    score_cols = ['tfidf_score', 'sbert_score', 'two_tower_score']
    for col in score_cols:
        if col not in combined_recs:
            combined_recs[col] = 0
    combined_recs[score_cols] = combined_recs[score_cols].fillna(0)

    # Normalize scores to a 0-1 scale to ensure fair weighting
    for col in score_cols:
        max_score = combined_recs[col].max()
        if max_score > 0:
            combined_recs[col] = combined_recs[col] / max_score

    # Calculate final hybrid score with weights
    combined_recs['combined_score'] = (
        0.3 * combined_recs['tfidf_score'] +
        0.4 * combined_recs['sbert_score'] +
        0.3 * combined_recs['two_tower_score']
    )

    # Sort by the final combined score and return the top N results
    return combined_recs.sort_values(by='combined_score', ascending=False).head(top_n)

def semantic_skill_similarity(user_skills, course_skills, threshold=0.7):
    """Calculate semantic similarity between user skills and course skills"""
    if not user_skills or not course_skills or not loaded_sbert_model:
        return False, 0.0
    
    try:
        # Get embeddings for user skills
        user_skill_embeddings = []
        for skill in user_skills:
            if skill.strip():
                embedding = loaded_sbert_model.encode(skill.strip())
                user_skill_embeddings.append(embedding)
        
        if not user_skill_embeddings:
            return False, 0.0
        
        # Get embeddings for course skills
        course_skill_embeddings = []
        for skill in course_skills:
            if isinstance(skill, str) and skill.strip():
                embedding = loaded_sbert_model.encode(skill.strip())
                course_skill_embeddings.append(embedding)
        
        if not course_skill_embeddings:
            return False, 0.0
        
        # Calculate maximum similarity for each user skill
        max_similarities = []
        for user_emb in user_skill_embeddings:
            similarities = []
            for course_emb in course_skill_embeddings:
                sim = np.dot(user_emb, course_emb) / (np.linalg.norm(user_emb) * np.linalg.norm(course_emb))
                similarities.append(sim)
            max_similarities.append(max(similarities))
        
        # Use average of maximum similarities
        avg_similarity = np.mean(max_similarities)
        has_match = avg_similarity >= threshold
        
        return has_match, avg_similarity
        
    except Exception as e:
        print(f"Error in semantic skill matching: {e}")
        return False, 0.0

def filter_courses_enhanced(df, level=None, providers=None, skills=None, duration_pref=None, 
                          skill_similarity_threshold=0.7, enable_fuzzy_skills=True):
    """Enhanced filtering with semantic skill matching"""
    if df is None: 
        return pd.DataFrame()
    filtered_df = df.copy()
    
    # Filter by level with hierarchy support
    if level and level.lower() != "all levels":
        level_hierarchy = {
            'beginner': ['beginner'],
            'intermediate': ['beginner', 'intermediate'],  # Include beginner for intermediate users
            'advanced': ['beginner', 'intermediate', 'advanced']  # Include all for advanced users
        }
        
        if level.lower() in level_hierarchy:
            allowed_levels = level_hierarchy[level.lower()]
            filtered_df = filtered_df[filtered_df["level"].str.lower().isin(allowed_levels)]
    
    # Filter by provider
    if providers and isinstance(providers, list) and len(providers) > 0:
        filtered_df = filtered_df[filtered_df["provider"].isin(providers)]
    
    # Enhanced skills filtering with semantic matching
    if skills and isinstance(skills, list) and len(skills) > 0:
        print(f"\nFiltering by skills: {skills}")
        skills_lower = [s.lower().strip() for s in skills]
        print(f"Normalized skills to search for: {skills_lower}")
        
        def has_required_skills_enhanced(course_skills):
            if not isinstance(course_skills, list):
                return False
            
            # First try exact matching (faster)
            course_skills_lower = [s.lower().strip() for s in course_skills if isinstance(s, str)]
            exact_matches = any(req_skill in course_skills_lower for req_skill in skills_lower)
            
            if exact_matches:
                return True
            
            # If no exact matches and fuzzy matching is enabled
            if enable_fuzzy_skills:
                has_semantic_match, similarity_score = semantic_skill_similarity(
                    skills_lower, course_skills, skill_similarity_threshold
                )
                if has_semantic_match:
                    print(f"Semantic skill match found with similarity: {similarity_score:.3f}")
                return has_semantic_match
            
            return False
            
        filtered_df = filtered_df[filtered_df["skills_list"].apply(has_required_skills_enhanced)]
        print(f"After enhanced skills filtering: {len(filtered_df)} courses remaining")
    
    # Smart duration filtering with flexibility
    if duration_pref:
        filtered_df["duration"] = pd.to_numeric(filtered_df["duration"], errors="coerce")
        if duration_pref == "short": 
            # Prefer short but allow medium if highly rated
            short_courses = filtered_df[filtered_df["duration"] <= 10]
            medium_highly_rated = filtered_df[
                (filtered_df["duration"] > 10) & 
                (filtered_df["duration"] <= 25) & 
                (filtered_df["adjusted_rating"] >= 4.5)
            ]
            filtered_df = pd.concat([short_courses, medium_highly_rated]).drop_duplicates()
        elif duration_pref == "medium": 
            filtered_df = filtered_df[
                (filtered_df["duration"] > 5) & (filtered_df["duration"] <= 50)
            ]
        elif duration_pref == "long": 
            filtered_df = filtered_df[filtered_df["duration"] > 30]
    
    return filtered_df

def diversify_recommendations(recommendations_df, diversity_weight=0.3, max_similar_skills=0.8):
    """Select diverse recommendations using skill-based diversity"""
    if recommendations_df.empty or len(recommendations_df) <= 2:
        return recommendations_df
    
    try:
        # Get course embeddings for diversity calculation
        selected_courses = []
        remaining_courses = recommendations_df.copy()
        
        # Always select the top-ranked course first
        top_course = remaining_courses.iloc[0]
        selected_courses.append(top_course)
        remaining_courses = remaining_courses.iloc[1:]
        
        # Select remaining courses balancing relevance and diversity
        while len(selected_courses) < min(5, len(recommendations_df)) and not remaining_courses.empty:
            best_score = -1
            best_idx = 0
            
            for idx, candidate in remaining_courses.iterrows():
                # Original relevance score (normalized)
                relevance_score = 0
                score_cols = ['tfidf_score', 'sbert_score', 'two_tower_score', 'combined_score']
                for col in score_cols:
                    if col in candidate and pd.notna(candidate[col]):
                        relevance_score = max(relevance_score, candidate[col])
                
                # Calculate diversity score
                diversity_score = 1.0
                if 'skills_list' in candidate and isinstance(candidate['skills_list'], list):
                    candidate_skills = candidate['skills_list']
                    
                    # Compare with already selected courses
                    min_diversity = 1.0
                    for selected in selected_courses:
                        if 'skills_list' in selected and isinstance(selected['skills_list'], list):
                            selected_skills = selected['skills_list']
                            
                            # Calculate skill overlap
                            if candidate_skills and selected_skills:
                                common_skills = set(candidate_skills) & set(selected_skills)
                                union_skills = set(candidate_skills) | set(selected_skills)
                                if union_skills:
                                    jaccard_similarity = len(common_skills) / len(union_skills)
                                    skill_diversity = 1.0 - jaccard_similarity
                                    min_diversity = min(min_diversity, skill_diversity)
                    
                    diversity_score = min_diversity
                
                # Combined score: relevance + diversity
                combined_score = (1 - diversity_weight) * relevance_score + diversity_weight * diversity_score
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_idx = idx
            
            # Add the best diverse candidate
            if best_idx in remaining_courses.index:
                selected_courses.append(remaining_courses.loc[best_idx])
                remaining_courses = remaining_courses.drop(best_idx)
        
        # Convert back to DataFrame
        if selected_courses:
            return pd.DataFrame(selected_courses).reset_index(drop=True)
        else:
            return recommendations_df
            
    except Exception as e:
        print(f"Error in diversification: {e}")
        return recommendations_df

def adaptive_weight_learning(query_text, skills, level, duration_pref):
    """Adaptively adjust model weights based on query characteristics"""
    weights = {'tfidf': 0.3, 'sbert': 0.4, 'two_tower': 0.3}  # Default weights
    
    try:
        # Adjust based on query characteristics
        if query_text:
            query_length = len(query_text.split())
            if query_length > 10:  # Long descriptive queries - favor SBERT
                weights['sbert'] += 0.1
                weights['tfidf'] -= 0.05
                weights['two_tower'] -= 0.05
            elif query_length <= 3:  # Short queries - favor TF-IDF
                weights['tfidf'] += 0.1
                weights['sbert'] -= 0.05
                weights['two_tower'] -= 0.05
        
        # Adjust based on skills specificity
        if skills and len(skills) > 3:  # Many skills - favor Two-Tower (better at complex preferences)
            weights['two_tower'] += 0.1
            weights['sbert'] -= 0.05
            weights['tfidf'] -= 0.05
        
        # Adjust based on level specificity
        if level and level.lower() in ['beginner', 'advanced']:  # Specific levels
            weights['two_tower'] += 0.05
            weights['sbert'] -= 0.025
            weights['tfidf'] -= 0.025
        
        # Ensure weights sum to 1
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        print(f"Adaptive weights: {weights}")
        return weights
        
    except Exception as e:
        print(f"Error in adaptive weighting: {e}")
        return {'tfidf': 0.3, 'sbert': 0.4, 'two_tower': 0.3}

def estimate_course_difficulty(course_row):
    """Estimate course difficulty based on various factors"""
    try:
        difficulty_score = 0.0
        
        # Level-based difficulty
        level = str(course_row.get('level', '')).lower()
        if 'beginner' in level:
            difficulty_score += 1.0
        elif 'intermediate' in level:
            difficulty_score += 2.0
        elif 'advanced' in level:
            difficulty_score += 3.0
        else:
            difficulty_score += 1.5  # Default
        
        # Duration-based difficulty (longer courses tend to be more comprehensive)
        duration = course_row.get('duration', 0)
        if pd.notna(duration) and duration > 0:
            if duration > 50:
                difficulty_score += 1.0
            elif duration > 20:
                difficulty_score += 0.5
        
        # Skills complexity (more skills = potentially more complex)
        skills = course_row.get('skills_list', [])
        if isinstance(skills, list):
            if len(skills) > 5:
                difficulty_score += 0.5
            elif len(skills) > 10:
                difficulty_score += 1.0
        
        # Title complexity indicators
        title = str(course_row.get('title', '')).lower()
        complexity_keywords = ['advanced', 'expert', 'master', 'complete', 'comprehensive', 'deep dive']
        beginner_keywords = ['intro', 'basics', 'fundamentals', 'getting started', 'beginner']
        
        for keyword in complexity_keywords:
            if keyword in title:
                difficulty_score += 0.5
                
        for keyword in beginner_keywords:
            if keyword in title:
                difficulty_score -= 0.5
        
        # Normalize to 1-5 scale
        difficulty_score = max(1.0, min(5.0, difficulty_score))
        return difficulty_score
        
    except Exception as e:
        print(f"Error estimating difficulty: {e}")
        return 2.5  # Default medium difficulty

def analyze_query_intent(query_text, skills, level):
    """Analyze user query to understand learning intent"""
    intent_features = {
        'learning_intent': 'general',  # general, specific_skill, career_change, certification
        'urgency': 'normal',           # urgent, normal, flexible
        'depth_preference': 'medium'   # shallow, medium, deep
    }
    
    if not query_text:
        return intent_features
    
    try:
        query_lower = query_text.lower()
        
        # Detect learning intent
        if any(word in query_lower for word in ['certification', 'certificate', 'exam', 'test']):
            intent_features['learning_intent'] = 'certification'
        elif any(word in query_lower for word in ['career', 'job', 'professional', 'work']):
            intent_features['learning_intent'] = 'career_change'
        elif skills and len(skills) > 0:
            intent_features['learning_intent'] = 'specific_skill'
        
        # Detect urgency
        if any(word in query_lower for word in ['quick', 'fast', 'crash course', 'urgent']):
            intent_features['urgency'] = 'urgent'
        elif any(word in query_lower for word in ['comprehensive', 'thorough', 'detailed']):
            intent_features['urgency'] = 'flexible'
        
        # Detect depth preference
        if any(word in query_lower for word in ['basics', 'intro', 'overview', 'quick']):
            intent_features['depth_preference'] = 'shallow'
        elif any(word in query_lower for word in ['deep', 'comprehensive', 'master', 'expert']):
            intent_features['depth_preference'] = 'deep'
        
        return intent_features
        
    except Exception as e:
        print(f"Error analyzing query intent: {e}")
        return intent_features

def personalized_reranking(recommendations_df, query_text, skills, level, intent_features):
    """Re-rank recommendations based on personalized factors"""
    if recommendations_df.empty:
        return recommendations_df
    
    try:
        reranked_df = recommendations_df.copy()
        
        # Calculate difficulty scores
        reranked_df['difficulty_score'] = reranked_df.apply(estimate_course_difficulty, axis=1)
        
        # Adjust scores based on user intent
        for idx, row in reranked_df.iterrows():
            adjustment = 0.0
            
            # Intent-based adjustments
            if intent_features['learning_intent'] == 'certification':
                if 'certification' in str(row.get('title', '')).lower():
                    adjustment += 0.2
            elif intent_features['learning_intent'] == 'career_change':
                if row.get('adjusted_rating', 0) > 4.0:  # Prefer highly rated for career
                    adjustment += 0.1
            
            # Urgency-based adjustments
            if intent_features['urgency'] == 'urgent':
                duration = row.get('duration', 0)
                if pd.notna(duration) and duration <= 10:
                    adjustment += 0.15
            elif intent_features['urgency'] == 'flexible':
                duration = row.get('duration', 0)
                if pd.notna(duration) and duration > 30:
                    adjustment += 0.1
            
            # Depth preference adjustments
            difficulty = row.get('difficulty_score', 2.5)
            if intent_features['depth_preference'] == 'shallow' and difficulty <= 2.0:
                adjustment += 0.1
            elif intent_features['depth_preference'] == 'deep' and difficulty >= 4.0:
                adjustment += 0.1
            
            # Apply adjustment to combined score, or create it if it doesn't exist
            if 'combined_score' in reranked_df.columns:
                reranked_df.at[idx, 'combined_score'] += adjustment
            else:
                # Create combined_score if it doesn't exist, using the best available score
                best_score = 0
                for score_col in ['tfidf_score', 'sbert_score', 'two_tower_score']:
                    if score_col in row and pd.notna(row[score_col]):
                        best_score = max(best_score, float(row[score_col]))
                if 'combined_score' not in reranked_df.columns:
                    reranked_df['combined_score'] = 0
                reranked_df.at[idx, 'combined_score'] = best_score + adjustment
        
        # Re-sort by adjusted combined score
        if 'combined_score' in reranked_df.columns:
            reranked_df = reranked_df.sort_values(by='combined_score', ascending=False)
        else:
            reranked_df = reranked_df.sort_values(by='adjusted_rating', ascending=False)
        return reranked_df
        
    except Exception as e:
        print(f"Error in personalized reranking: {e}")
        return recommendations_df

