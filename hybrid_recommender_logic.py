import pandas as pd
import numpy as np
import pickle
import ast
import nltk # Keep for preprocessing function
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer # For type hinting, actual object loaded from pickle
from sklearn.metrics.pairwise import cosine_similarity
import re

# Ensure NLTK resources are available (assuming they were downloaded by the setup script)
# It's good practice to have this check or ensure it's run prior.
# For this script, we assume content_based_setup_v2.py has run successfully.

# --- Global Variables and Constants ---
DATA_PATH = "cleaned_courses_with_enhanced_skills.csv"
TFIDF_MATRIX_PATH = "tfidf_matrix.pkl"
TFIDF_VECTORIZER_PATH = "tfidf_vectorizer.pkl"

# --- Load Precomputed Data and Models ---
print("Loading precomputed data and models...")
try:
    df_courses = pd.read_csv(DATA_PATH)
    with open(TFIDF_MATRIX_PATH, "rb") as f:
        tfidf_matrix_courses = pickle.load(f)
    with open(TFIDF_VECTORIZER_PATH, "rb") as f:
        tfidf_vectorizer = pickle.load(f)
    print("Data and models loaded successfully.")
except FileNotFoundError as e:
    print(f"Error: A required file was not found: {e}. Please run the setup script first.")
    exit()
except Exception as e:
    print(f"An error occurred during loading: {e}")
    exit()

# Re-parse skills column to ensure it's a list of strings, handling potential stringified lists or NaNs
def parse_skills_for_filtering(skill_entry):
    if pd.isna(skill_entry):
        return []
    if isinstance(skill_entry, str):
        try:
            evaluated_list = ast.literal_eval(skill_entry)
            if isinstance(evaluated_list, list):
                return [str(s).lower() for s in evaluated_list if pd.notna(s) and str(s).lower() != 'nan']
            else:
                return [str(evaluated_list).lower()] if pd.notna(evaluated_list) and str(evaluated_list).lower() != 'nan' else []
        except (ValueError, SyntaxError):
            return [skill_entry.lower()] if skill_entry.lower() != 'nan' else []
    elif isinstance(skill_entry, list):
        return [str(s).lower() for s in skill_entry if pd.notna(s) and str(s).lower() != 'nan']
    return []

df_courses['skills'] = df_courses['skills'].apply(parse_skills_for_filtering)

# --- Text Preprocessing Function (reused from setup for query processing) ---
stemmer = PorterStemmer()
stop_words_list = stopwords.words("english")

def preprocess_text_query(text):
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters but keep important ones like hyphens and underscores
    text = re.sub(r'[^a-z0-9\s\-_]', ' ', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stop words and stem, but preserve important technical terms
    processed_tokens = []
    for token in tokens:
        if token not in stop_words_list:
            # Don't stem if it's a technical term or programming language
            if token in ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'rust', 'go', 'r', 'matlab', 'scala', 'perl', 'haskell', 'lua', 'typescript', 'dart', 'sql', 'html', 'css', 'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring', 'tensorflow', 'pytorch', 'keras', 'numpy', 'pandas', 'scipy', 'sklearn', 'git', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'linux', 'unix', 'windows', 'macos', 'ios', 'android']:
                processed_tokens.append(token)
            else:
                processed_tokens.append(stemmer.stem(token))
    
    return " ".join(processed_tokens)

# --- Core Recommender Functions ---

def get_content_based_scores(query_text, vectorizer, course_matrix, df_indices):
    """Calculates cosine similarity scores for a query against course text features."""
    if not query_text:
        return pd.Series(dtype='float64')
    processed_query = preprocess_text_query(query_text)
    query_vector = vectorizer.transform([processed_query])
    cosine_similarities = cosine_similarity(query_vector, course_matrix[df_indices])
    return pd.Series(cosine_similarities[0], index=df_indices)

def filter_courses(df, level=None, providers=None, required_skills=None, duration_min=None, duration_max=None):
    """Applies structured filters to the DataFrame."""
    filtered_df = df.copy()
    
    if level:
        filtered_df = filtered_df[filtered_df['level'].notna() & filtered_df['level'].str.contains(level, case=False, na=False)]
    
    if providers and isinstance(providers, list) and len(providers) > 0:
        filtered_df = filtered_df[filtered_df['provider'].notna() & filtered_df['provider'].isin(providers)]
        
    if required_skills and isinstance(required_skills, list) and len(required_skills) > 0:
        required_skills_lower = [skill.lower() for skill in required_skills]
        def has_all_skills(course_skills_list):
            if not course_skills_list: # Handles empty list from parsing NaN
                return False
            return all(req_skill in course_skills_list for req_skill in required_skills_lower)
        filtered_df = filtered_df[filtered_df['skills'].apply(has_all_skills)]

    if duration_min is not None:
        filtered_df = filtered_df[filtered_df['duration'].notna() & (filtered_df['duration'] >= duration_min)]
    if duration_max is not None:
        filtered_df = filtered_df[filtered_df['duration'].notna() & (filtered_df['duration'] <= duration_max)]
        
    return filtered_df

def recommend_courses(query_text=None, level=None, providers=None, skills=None, 
                      duration_min=None, duration_max=None, top_n=5):
    """Hybrid recommendation logic."""
    
    # 1. Apply structured filters
    candidate_courses = filter_courses(df_courses, level, providers, skills, duration_min, duration_max)
    
    if candidate_courses.empty:
        return pd.DataFrame() # No courses match filters

    candidate_indices = candidate_courses.index.tolist()
    
    # 2. Calculate content-based scores if query_text is provided
    if query_text:
        # Get TF-IDF scores
        content_scores = get_content_based_scores(query_text, tfidf_vectorizer, tfidf_matrix_courses, candidate_indices)
        candidate_courses['content_score'] = content_scores.reindex(candidate_courses.index).fillna(0)
        
        # Get SBERT scores if available
        try:
            from sbert_recommender_component import get_sbert_recommendations
            sbert_recs = get_sbert_recommendations(query_text, top_n=len(candidate_courses))
            if not sbert_recs.empty:
                sbert_scores = pd.Series(sbert_recs['sbert_similarity_score'].values, 
                                       index=sbert_recs.index)
                candidate_courses['sbert_score'] = sbert_scores.reindex(candidate_courses.index).fillna(0)
                
                # Combine scores (weighted average)
                candidate_courses['combined_score'] = (
                    0.4 * candidate_courses['content_score'] + 
                    0.6 * candidate_courses['sbert_score'] +
                    0.2 * candidate_courses['adjusted_rating'].fillna(0)
                )
            else:
                candidate_courses['combined_score'] = candidate_courses['content_score']
        except Exception as e:
            print(f"SBERT scoring failed: {e}. Using only TF-IDF scores.")
            candidate_courses['combined_score'] = candidate_courses['content_score']
    else:
        # No query, use only rating
        candidate_courses['combined_score'] = candidate_courses['adjusted_rating'].fillna(0)

    # 3. Sort by combined score
    ranked_courses = candidate_courses.sort_values(by='combined_score', ascending=False)
    
    # 4. Select top N and desired columns
    recommendations = ranked_courses.head(top_n)    
    output_columns = ['title', 'provider', 'url', 'level', 'skills', 'adjusted_rating', 'duration', 'combined_score']
    if 'content_score' in recommendations.columns:
        output_columns.append('content_score')
    if 'sbert_score' in recommendations.columns:
        output_columns.append('sbert_score')
            
    return recommendations[output_columns]

# --- Example Usage (for testing the logic directly) ---
if __name__ == "__main__":
    print("\n--- Testing Hybrid Recommender Logic ---")
    
    # Test Case 1: Free-text query only
    print("\nTest Case 1: Free-text query 'beginner python data analysis'")
    recs1 = recommend_courses(query_text="beginner python data analysis", top_n=3)
    print(recs1)

    # Test Case 2: Structured filters only
    print("\nTest Case 2: Level 'Beginner', Provider 'Udemy'")
    recs2 = recommend_courses(level="Beginner", providers=["Udemy"], top_n=3)
    print(recs2)

    # Test Case 3: Hybrid - free-text and structured
    print("\nTest Case 3: Query 'machine learning algorithms', Skills ['python'], Level 'Intermediate'")
    recs3 = recommend_courses(query_text="machine learning algorithms", skills=["python"], level="Intermediate", top_n=3)
    print(recs3)
    
    # Test Case 4: Filter by duration
    print("\nTest Case 4: Query 'short introduction to javascript', Duration Max 10 hours")
    recs4 = recommend_courses(query_text="short introduction to javascript", duration_max=10, top_n=3)
    print(recs4)

    # Test Case 5: No results expected
    print("\nTest Case 5: Highly specific filters likely yielding no results")
    recs5 = recommend_courses(level="Expert", providers=["NonExistentProvider"], skills=["ObscureSkill123"], top_n=3)
    print(recs5)

    print("\nHybrid recommender logic script finished.")

