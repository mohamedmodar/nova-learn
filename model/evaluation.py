import pandas as pd
import numpy as np
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import warnings

# --- Suppress specific warnings for cleaner output ---
warnings.filterwarnings("ignore", category=UserWarning, module='tensorflow')

# --- Import components from the main recommender system ---
# We need the main recommendation function and the course data/models
try:
    from recommender_interface_advanced_v6 import (
        get_recommendations,
        df_all_courses,
        tfidf_vectorizer,
        tfidf_matrix,
        preprocess_text_for_tfidf
    )
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"FATAL: Could not import necessary components from recommender_interface_advanced_v6.py. Error: {e}")
    print("Please ensure the script is in the same directory and all dependencies are installed.")
    IMPORTS_SUCCESSFUL = False

# --- Configuration ---
K = 10  # The "k" in NDCG@k, number of recommendations to evaluate
TEST_SET_SIZE = 50  # Number of queries to generate for the test set
SIMILARITY_THRESHOLD = 0.3 # TF-IDF score threshold to be considered 'ground truth'

# --- Evaluation Metrics ---

def ndcg_at_k(true_relevance, recommended_item_ids, k=K):
    """
    Calculates the Normalized Discounted Cumulative Gain (NDCG) at k.
    
    Args:
        true_relevance (set): A set of item_ids that are truly relevant.
        recommended_item_ids (list): A list of recommended item_ids.
        k (int): The number of recommendations to consider.
        
    Returns:
        float: The NDCG score.
    """
    recommended_item_ids = recommended_item_ids[:k]
    
    # Calculate DCG (Discounted Cumulative Gain)
    dcg = 0
    for i, item_id in enumerate(recommended_item_ids):
        if item_id in true_relevance:
            # Relevance is 1 if in the set, 0 otherwise.
            # The gain is 1, discounted by log2(rank+1). Rank is i+1.
            dcg += 1 / np.log2(i + 2) # i+2 because rank is 1-based (i+1)
            
    # Calculate IDCG (Ideal Discounted Cumulative Gain)
    # This is the DCG score if the recommendations were perfectly ordered.
    ideal_k = min(k, len(true_relevance))
    idcg = sum([1 / np.log2(i + 2) for i in range(ideal_k)])
    
    if idcg == 0:
        return 0.0 # Avoid division by zero
        
    return dcg / idcg


# --- Test Set Generation ---

def generate_evaluation_test_set(size=TEST_SET_SIZE):
    """
    Generates a test set for evaluation.
    Each item in the test set consists of:
    - query_text: The title of a course.
    - ground_truth: A set of item_ids of other courses that are highly similar.
    - history_item: An item_id from the ground_truth set to simulate user history.
    """
    if df_all_courses is None or tfidf_matrix is None:
        print("Cannot generate test set. Course data or TF-IDF matrix not loaded.")
        return []

    test_set = []
    
    print(f"\n--- Generating evaluation test set of size {size}... ---")
    
    # Select random courses to act as the basis for our queries
    # Ensure there's enough data to sample from
    if len(df_all_courses) < size:
        print(f"Warning: Requested test set size ({size}) is larger than the number of courses ({len(df_all_courses)}). Using all courses.")
        size = len(df_all_courses)
        
    sample_courses = df_all_courses.sample(n=size, random_state=42)

    for _, row in tqdm(sample_courses.iterrows(), total=size, desc="Building Test Set"):
        query_text = row['title']
        query_item_id = row['item_id']
        
        # Find similar items using TF-IDF to create the ground truth
        # This uses the pre-processed text from the main script's TF-IDF matrix
        query_vector = tfidf_vectorizer.transform([preprocess_text_for_tfidf(query_text)])
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # Get indices of items above a similarity threshold
        relevant_indices = np.where(similarities > SIMILARITY_THRESHOLD)[0]
        
        # Create the ground truth set of item_ids, excluding the query item itself
        ground_truth_ids = set(df_all_courses.iloc[relevant_indices]['item_id'])
        ground_truth_ids.discard(query_item_id)
        
        # We need at least one relevant item for a valid test case
        if not ground_truth_ids:
            continue
            
        # Select one item from the ground truth to act as a "liked" item for personalization tests
        history_item = np.random.choice(list(ground_truth_ids))

        test_set.append({
            "query_text": query_text,
            "ground_truth": ground_truth_ids,
            "history_item": history_item
        })
        
    print(f"--- Successfully generated a test set with {len(test_set)} valid queries. ---")
    return test_set

# --- Main Evaluation Function ---

def evaluate_models():
    """
    Runs the full evaluation pipeline:
    1. Generates the test set.
    2. Runs recommendations for each model.
    3. Calculates NDCG@k for each.
    4. Compares non-personalized vs. personalized results.
    5. Prints a summary report.
    """
    test_set = generate_evaluation_test_set()
    if not test_set:
        return

    results = []
    
    models_to_evaluate = ['tfidf', 'sbert', 'two_tower', 'hybrid']

    for test_case in tqdm(test_set, desc="Evaluating All Models"):
        query_text = test_case['query_text']
        ground_truth = test_case['ground_truth']
        history_item = test_case['history_item'] # For personalized tests
        
        case_results = {'query': query_text}

        # --- Evaluate Non-Personalized Models ---
        for model_name in models_to_evaluate:
            recs = get_recommendations(
                query_text=query_text,
                top_n=K,
                model_type=model_name
            )
            rec_ids = recs['item_id'].tolist() if not recs.empty else []
            score = ndcg_at_k(ground_truth, rec_ids, k=K)
            case_results[f'ndcg_{model_name}'] = score

        # --- Evaluate Personalized Models ---
        # We only evaluate the semantic models for personalization impact
        for model_name in ['sbert', 'two_tower', 'hybrid']:
            recs = get_recommendations(
                query_text=query_text,
                user_history=[history_item], # Add the simulated "like"
                top_n=K,
                model_type=model_name
            )
            rec_ids = recs['item_id'].tolist() if not recs.empty else []
            score = ndcg_at_k(ground_truth, rec_ids, k=K)
            case_results[f'ndcg_{model_name}_personalized'] = score
            
        results.append(case_results)
        
    # --- Analyze and Print Results ---
    results_df = pd.DataFrame(results)
    
    print("\n\n--- Recommender Model Evaluation Report ---")
    print(f"Based on {len(results_df)} test queries, with NDCG@{K}")
    print("--------------------------------------------------")
    
    summary = {}
    
    # Non-personalized scores
    for model_name in models_to_evaluate:
        col_name = f'ndcg_{model_name}'
        summary[model_name] = results_df[col_name].mean()
        
    # Personalized scores
    for model_name in ['sbert', 'two_tower', 'hybrid']:
        col_name = f'ndcg_{model_name}_personalized'
        summary[f'{model_name}_personalized'] = results_df[col_name].mean()
        
    summary_df = pd.DataFrame.from_dict(summary, orient='index', columns=['Average NDCG Score'])
    summary_df = summary_df.sort_values(by='Average NDCG Score', ascending=False)
    
    # Improve formatting
    summary_df['Average NDCG Score'] = summary_df['Average NDCG Score'].map('{:.4f}'.format)

    print(summary_df)
    
    print("\n\n--- Personalization Impact Analysis ---")
    print("Compares model performance with a relevant item in history vs. without.")
    
    # Create a list of dictionaries for the table
    pers_impact_data = []
    for model_name in ['sbert', 'two_tower', 'hybrid']:
        base_score = summary.get(model_name, 0)
        pers_score = summary.get(f'{model_name}_personalized', 0)
        improvement = pers_score - base_score
        improvement_percent_str = ""
        if base_score > 0:
            improvement_percent = (improvement / base_score) * 100
            improvement_percent_str = f"{improvement_percent:+.2f}%"

        pers_impact_data.append({
            "Model": model_name.upper(),
            "Base Score": f"{base_score:.4f}",
            "Personalized Score": f"{pers_score:.4f}",
            "Change": f"{improvement:+.4f}",
            "% Change": improvement_percent_str
        })
    
    pers_impact_df = pd.DataFrame(pers_impact_data)
    print(pers_impact_df.to_string(index=False))
    print("--------------------------------------------------")


if __name__ == "__main__":
    if IMPORTS_SUCCESSFUL:
        print("Starting the model evaluation script...")
        # Check if we can run
        if df_all_courses is not None and tfidf_vectorizer is not None:
             evaluate_models()
        else:
            print("\nFATAL: Cannot run evaluation because course data or TF-IDF models failed to load in the main interface.")
    else:
        print("\nEvaluation script cannot run due to import failures.") 