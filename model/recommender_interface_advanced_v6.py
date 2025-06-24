import pandas as pd
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import torch
import tensorflow as tf
from sentence_transformers import SentenceTransformer, util
import re

# --- Import components from other scripts ---
from sbert_recommender_component import sbert_model as loaded_sbert_model, course_embeddings_tensor as loaded_sbert_course_embeddings
from adapted_two_tower_model import CourseRecommender

# --- Configuration ---
TFIDF_VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"
TFIDF_MATRIX_PATH = "models/tfidf_matrix.pkl"
COURSE_DATA_PATH = "data/final(final).csv"
SBERT_COURSE_EMBEDDINGS_FOR_TT_PATH = "models/course_sbert_embeddings.pkl"
TWO_TOWER_MODEL_PATH = 'models/two_tower_content_based.weights.h5'

# --- Global Variables / Load Models ---
print("Loading TF-IDF components...")
try:
    with open(TFIDF_VECTORIZER_PATH, "rb") as f:
        tfidf_vectorizer = pickle.load(f)
    with open(TFIDF_MATRIX_PATH, "rb") as f:
        tfidf_matrix = pickle.load(f)
    print("TF-IDF vectorizer and matrix loaded.")
except Exception as e:
    print(f"Warning: Could not load TF-IDF components: {e}")
    tfidf_vectorizer, tfidf_matrix = None, None

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

# --- Initialize the Main Two-Tower Recommender Class ---
print("\nInitializing the main Course Recommender for Two-Tower model...")
if df_all_courses is not None and all_item_sbert_embeddings_tensor_for_tt is not None:
    main_recommender = CourseRecommender(
        courses_df=df_all_courses,
        course_sbert_embeddings=all_item_sbert_embeddings_tensor_for_tt,
        model_path=TWO_TOWER_MODEL_PATH
    )
    if main_recommender.item_embeddings_norm is None:
        print("WARNING: Two-Tower model weights could not be loaded. Two-Tower and Hybrid models will not work.")
else:
    main_recommender = None
    print("WARNING: Two-Tower recommender could not be initialized.")

# --- Text Preprocessing for TF-IDF ---
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
stemmer = PorterStemmer()
stop_words = set(stopwords.words("english"))
def preprocess_text_for_tfidf(text):
    if not isinstance(text, str): return ""
    text = re.sub(r"\W", " ", text.lower())
    tokens = text.split()
    stemmed_tokens = [stemmer.stem(word) for word in tokens if word not in stop_words]
    return " ".join(stemmed_tokens)

# --- Individual Model Functions (Updated for Intent Vector) ---

def _get_tfidf_recs(query, candidate_df, top_n=10, threshold=0.0):
    if tfidf_vectorizer is None or tfidf_matrix is None or not query: return pd.DataFrame()
    processed_query = preprocess_text_for_tfidf(query)
    query_vector = tfidf_vectorizer.transform([processed_query])
    
    candidate_indices = candidate_df.index.tolist()
    candidate_tfidf_matrix = tfidf_matrix[candidate_indices]
    
    cosine_similarities = cosine_similarity(query_vector, candidate_tfidf_matrix).flatten()
    
    recs = candidate_df.copy()
    recs['tfidf_score'] = cosine_similarities
    
    # --- BUG FIX: Only keep results above a certain similarity threshold ---
    recs = recs[recs['tfidf_score'] > threshold]
    
    return recs.sort_values(by='tfidf_score', ascending=False).head(top_n)

def _get_sbert_recs(candidate_df, top_n=10, query=None, intent_vector=None):
    if loaded_sbert_model is None or loaded_sbert_course_embeddings is None: return pd.DataFrame()
    if candidate_df.empty: return pd.DataFrame()

    if intent_vector is not None:
        query_embedding = intent_vector
    elif query:
        query_embedding = loaded_sbert_model.encode(query, convert_to_tensor=True)
    else:
        return pd.DataFrame() # Cannot search without a query or vector

    candidate_indices = candidate_df.index.tolist()
    candidate_embeddings = torch.index_select(loaded_sbert_course_embeddings, 0, torch.tensor(candidate_indices, dtype=torch.long))

    cosine_scores = util.cos_sim(query_embedding, candidate_embeddings)[0]

    recs = candidate_df.copy()
    recs['sbert_score'] = cosine_scores.cpu().numpy()
    return recs.sort_values(by='sbert_score', ascending=False).head(top_n)

def _get_two_tower_recs(candidate_df, top_n=10, query=None, intent_vector=None):
    if main_recommender is None or main_recommender.item_embeddings_norm is None: return pd.DataFrame()
    
    if intent_vector is not None:
        # Convert PyTorch intent_vector to TensorFlow tensor
        query_embedding_tf = tf.expand_dims(tf.convert_to_tensor(intent_vector.cpu().numpy()), axis=0)
    elif query:
        # Fallback to encoding the raw query text
        query_embedding = sbert_model_for_query.encode(query, convert_to_tensor=True)
        query_embedding_tf = tf.expand_dims(tf.convert_to_tensor(query_embedding.numpy()), axis=0)
    else:
        return pd.DataFrame() # Cannot search

    user_vector = main_recommender.model.query_tower(query_embedding_tf)
    user_vector_norm = tf.nn.l2_normalize(user_vector, axis=-1)
    
    similarity_scores = tf.matmul(user_vector_norm, main_recommender.item_embeddings_norm, transpose_b=True)
    similarity_scores = tf.squeeze(similarity_scores, axis=0).numpy()

    candidate_indices = candidate_df.index.tolist()
    candidate_scores = similarity_scores[candidate_indices]
    
    recs = candidate_df.copy()
    recs['two_tower_score'] = candidate_scores
    return recs.sort_values(by='two_tower_score', ascending=False).head(top_n)

def _get_hybrid_recs(candidate_df, top_n=10, query=None, intent_vector=None):
    # TF-IDF uses the raw text query
    tfidf_recs = _get_tfidf_recs(query, candidate_df, top_n=20)
    
    # SBERT and Two-Tower use the powerful intent_vector if available
    sbert_recs = _get_sbert_recs(candidate_df, top_n=20, query=query, intent_vector=intent_vector)
    two_tower_recs = _get_two_tower_recs(candidate_df, top_n=20, query=query, intent_vector=intent_vector)
    
    combined = pd.concat([tfidf_recs, sbert_recs, two_tower_recs])
    all_indices = combined.index.unique()
    
    # --- BUG FIX: Use the pre-filtered candidate_df, not the entire df_all_courses ---
    combined_recs = candidate_df.loc[all_indices].copy()
    
    for rec_df, score_name in [(tfidf_recs, 'tfidf_score'), (sbert_recs, 'sbert_score'), (two_tower_recs, 'two_tower_score')]:
        if not rec_df.empty:
            combined_recs = combined_recs.join(rec_df[[score_name]])
    
    combined_recs.fillna(0, inplace=True)
    
    for col in ['tfidf_score', 'sbert_score', 'two_tower_score']:
        if col in combined_recs.columns:
            max_score = combined_recs[col].max()
            if max_score > 0:
                combined_recs[col] = combined_recs[col] / max_score
            
    combined_recs['combined_score'] = (
        0.2 * combined_recs.get('tfidf_score', 0) +
        0.4 * combined_recs.get('sbert_score', 0) +
        0.4 * combined_recs.get('two_tower_score', 0)
    )
    
    return combined_recs.sort_values(by='combined_score', ascending=False).head(top_n)

# --- Main Recommendation Function ---

def get_recommendations(
    query_text=None, level=None, skills=None, providers=None,
    top_n=10, user_history=None, disliked_history=None, model_type='hybrid', duration_pref=None,
    candidate_threshold=0.1
):
    if df_all_courses is None: return pd.DataFrame()

    # 1. Initial Filtering based on structured criteria (level, skills, etc.)
    filtered_df = filter_courses(df_all_courses, level, providers, skills, duration_pref)
    
    if disliked_history:
        filtered_df = filtered_df[~filtered_df['item_id'].isin(disliked_history)]

    if filtered_df.empty: return pd.DataFrame()

    final_query_text = query_text.strip() if query_text else ""
    
    # --- UPDATED: Two-Stage "Filter then Re-rank" Logic ---
    
    # Stage 1: Generate a relevant candidate set using ONLY the user's text query
    candidate_generation_query = final_query_text
    
    candidate_df = pd.DataFrame()
    if candidate_generation_query.strip():
        print(f"--- Stage 1: Filtering candidates with text query: '{candidate_generation_query}' ---")
        # Get a larger set of candidates (e.g., 200) from the entire dataset using TF-IDF
        all_candidates = _get_tfidf_recs(
            candidate_generation_query, 
            df_all_courses, 
            top_n=200,
            threshold=candidate_threshold
        )
        
        # Now, filter these relevant candidates by the user's structured filters (level, etc.)
        candidate_ids = all_candidates.index.intersection(filtered_df.index)
        candidate_df = filtered_df.loc[candidate_ids]
        print(f"--- Found {len(candidate_df)} relevant candidates after filtering. ---")
    else:
        # If no keywords, the initial filtered_df is our only candidate set
        candidate_df = filtered_df

    if candidate_df.empty:
        print("--- No candidates found after keyword filtering. ---")
        return pd.DataFrame()

    # Stage 2: Re-rank the relevant candidates using personalized semantic models
    
    # Create a personalized keyword query for the TF-IDF re-ranking score in the hybrid model
    personalized_keyword_query = final_query_text
    if user_history:
        liked_titles = df_all_courses[df_all_courses['item_id'].isin(user_history)]['title'].tolist()
        if liked_titles:
            personalized_keyword_query = f"{personalized_keyword_query} {' '.join(liked_titles)}"

    intent_vector = None
    if final_query_text or user_history:
        # This logic for creating the intent_vector remains the same
        positive_embeddings_list = []
        if user_history:
            liked_indices = df_all_courses[df_all_courses['item_id'].isin(user_history)].index.tolist()
            if liked_indices:
                liked_embeddings = torch.index_select(loaded_sbert_course_embeddings, 0, torch.tensor(liked_indices, dtype=torch.long))
                positive_embeddings_list.append(liked_embeddings)
        if final_query_text:
            query_embedding = loaded_sbert_model.encode(final_query_text, convert_to_tensor=True)
            positive_embeddings_list.append(query_embedding.unsqueeze(0)); positive_embeddings_list.append(query_embedding.unsqueeze(0))

        if positive_embeddings_list:
            positive_vector = torch.mean(torch.cat(positive_embeddings_list, dim=0), dim=0)
            intent_vector = positive_vector
            if disliked_history:
                disliked_indices = df_all_courses[df_all_courses['item_id'].isin(disliked_history)].index.tolist()
                if disliked_indices:
                    disliked_embeddings = torch.index_select(loaded_sbert_course_embeddings, 0, torch.tensor(disliked_indices, dtype=torch.long))
                    negative_vector = torch.mean(disliked_embeddings, dim=0)
                    intent_vector = intent_vector - negative_vector

    # If no intent could be formed, fallback to top-rated among candidates
    if intent_vector is None:
        print("--- No personalization vector, returning top-rated from candidates. ---")
        return candidate_df.sort_values(by="adjusted_rating", ascending=False).head(top_n)

    print(f"--- Stage 2: Re-ranking {len(candidate_df)} candidates with '{model_type.upper()}' model. ---")
    
    # Dispatch to the correct model, now operating ONLY on the pre-filtered candidate_df
    if model_type == 'tfidf':
        # TF-IDF was already used for filtering, so we just re-rank with the personalized query
        return _get_tfidf_recs(personalized_keyword_query, candidate_df, top_n)
    elif model_type == 'sbert':
        return _get_sbert_recs(candidate_df, top_n, query=final_query_text, intent_vector=intent_vector)
    elif model_type == 'two_tower':
        return _get_two_tower_recs(candidate_df, top_n, query=final_query_text, intent_vector=intent_vector)
    else: # Hybrid
        return _get_hybrid_recs(candidate_df, top_n, query=personalized_keyword_query, intent_vector=intent_vector)

# Wrapper for GUI compatibility
def get_hybrid_recommendations_advanced(*args, **kwargs):
    return get_recommendations(*args, **kwargs)

# --- Helper Functions ---
def filter_courses(df, level=None, providers=None, skills=None, duration_pref=None):
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
    
    if duration_pref and duration_pref != "any":
        if "duration" in filtered_df.columns:
            # Ensure duration is numeric, coercing errors
            filtered_df["duration_numeric"] = pd.to_numeric(filtered_df["duration"], errors="coerce")
            
            if duration_pref == "short": # <= 10 hours
                filtered_df = filtered_df[filtered_df["duration_numeric"] <= 10]
            elif duration_pref == "medium": # 11-50 hours
                filtered_df = filtered_df[(filtered_df["duration_numeric"] > 10) & (filtered_df["duration_numeric"] <= 50)]
            elif duration_pref == "long": # > 50 hours
                filtered_df = filtered_df[filtered_df["duration_numeric"] > 50]
            
            # Drop the temporary numeric column
            filtered_df = filtered_df.drop(columns=["duration_numeric"])

    return filtered_df

# --- Example Usage ---
if __name__ == "__main__":
    print("\n--- Testing Simplified Recommender Interface ---")
    if df_all_courses is None:
        print("Cannot run tests as main course data failed to load.")
    else:
        # --- Define sample data for tests ---
        # Find some real item_ids from the dataset to make tests more realistic
        try:
            python_courses = df_all_courses[df_all_courses['title'].str.contains("Python", case=False, na=False)]
            js_courses = df_all_courses[df_all_courses['title'].str.contains("JavaScript", case=False, na=False)]
            
            history_item_1 = python_courses['item_id'].iloc[0] if not python_courses.empty else 'COURSE-165843-1111-FZ-PP'
            history_item_2 = python_courses['item_id'].iloc[1] if len(python_courses) > 1 else 'COURSE-269989-1224-FZ-PP'
            dislike_item_1 = js_courses['item_id'].iloc[0] if not js_courses.empty else 'COURSE-358588-1422-FZ-PP'

            test_history_py = [history_item_1, history_item_2]
            print(f"Using sample history items: {test_history_py}")
            print(f"Using sample dislike item: {dislike_item_1}")

        except Exception as e:
            print(f"Could not select sample items for tests, using defaults. Error: {e}")
            test_history_py = ['COURSE-165843-1111-FZ-PP', 'COURSE-269989-1224-FZ-PP']
            dislike_item_1 = 'COURSE-358588-1422-FZ-PP'


        print("\n\n--- Test 1: Simple Query-based Search ---")
        print("Query: 'learn machine learning with python'. Expect ML and Python courses.")
        print(get_recommendations(query_text="learn machine learning with python", top_n=3))

        print("\n\n--- Test 2: History-based Search (No Query) ---")
        print(f"History: Python courses. Expect recommendations related to Python.")
        print(get_recommendations(user_history=test_history_py, top_n=3))
        
        print(f"\n\n--- Test 3: Query Overriding History (Filter-then-Re-rank) ---")
        print("History: Python courses. Query: 'javascript fundamentals'.")
        print("EXPECT: Results MUST be about Javascript. History should only re-rank JS results.")
        print(get_recommendations(query_text="javascript fundamentals", user_history=test_history_py, top_n=3))

        print(f"\n\n--- Test 4: Structured Filters Only (No Query/History) ---")
        print("Filters: Beginner, Python. Expect beginner python courses.")
        print(get_recommendations(level="Beginner", skills=['python'], top_n=3))
        
        print(f"\n\n--- Test 5: Dislike Feature ---")
        print(f"Query: 'javascript'. Disliked item: A JavaScript course.")
        print(f"EXPECT: Recommendations for JavaScript, but EXCLUDING the disliked item '{dislike_item_1}'.")
        # First, show results WITHOUT the dislike
        print("--- (A) Results for 'javascript' WITHOUT dislike ---")
        recs_before_dislike = get_recommendations(query_text="javascript", top_n=3, model_type='sbert')
        print(recs_before_dislike)
        # Now, show results WITH the dislike
        print("\n--- (B) Results for 'javascript' WITH dislike ---")
        recs_after_dislike = get_recommendations(query_text="javascript", disliked_history=[dislike_item_1], top_n=3, model_type='sbert')
        print(recs_after_dislike)
        if not recs_before_dislike.empty and dislike_item_1 in recs_before_dislike['item_id'].values:
            print("VALIDATION: The disliked item was present in the original recommendations.")
        if not recs_after_dislike.empty and dislike_item_1 not in recs_after_dislike['item_id'].values:
            print("VALIDATION: The disliked item is correctly excluded from the new recommendations.")

        print("\n\n--- Test 6: Query with No Possible Results ---")
        print("Query: 'underwater basket weaving with neural networks'. Expect empty dataframe.")
        # We increase the threshold for this specific test to ensure no weak matches get through
        print(get_recommendations(
            query_text="underwater basket weaving with neural networks", 
            top_n=3,
            candidate_threshold=0.2
        ))
        
        print("\n\n--- Test 7: Personalization vs. Strict Filters ---")
        print("History: Advanced Python courses. Filter: 'Beginner' level.")
        print("EXPECT: ONLY Beginner level courses, even though history is advanced.")
        recs_with_filter = get_recommendations(user_history=test_history_py, level="Beginner", top_n=3)
        print(recs_with_filter)
        if not recs_with_filter.empty:
            all_beginner = recs_with_filter['level'].str.contains('Beginner', case=False).all()
            print(f"VALIDATION: All recommended courses are beginner level: {all_beginner}")

    print("\nRecommender interface script finished.")
