import pandas as pd
import numpy as np
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import warnings
import matplotlib.pyplot as plt
import altair as alt

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

def precision_at_k(true_relevance, recommended_item_ids, k=K):
    """
    Calculates Precision@k.
    Args:
        true_relevance (set): A set of item_ids that are truly relevant.
        recommended_item_ids (list): A list of recommended item_ids.
        k (int): The number of recommendations to consider.
    Returns:
        float: The Precision@k score.
    """
    recommended_item_ids = recommended_item_ids[:k]
    num_hits = sum(1 for item_id in recommended_item_ids if item_id in true_relevance)
    return num_hits / k if k > 0 else 0.0

def recall_at_k(true_relevance, recommended_item_ids, k=K):
    """
    Calculates Recall@k.
    Args:
        true_relevance (set): A set of item_ids that are truly relevant.
        recommended_item_ids (list): A list of recommended item_ids.
        k (int): The number of recommendations to consider.
    Returns:
        float: The Recall@k score.
    """
    recommended_item_ids = recommended_item_ids[:k]
    num_hits = sum(1 for item_id in recommended_item_ids if item_id in true_relevance)
    return num_hits / len(true_relevance) if len(true_relevance) > 0 else 0.0

def hit_rate_at_k(true_relevance, recommended_item_ids, k=K):
    """
    Calculates Hit Rate@k.
    Args:
        true_relevance (set): A set of item_ids that are truly relevant.
        recommended_item_ids (list): A list of recommended item_ids.
        k (int): The number of recommendations to consider.
    Returns:
        float: 1.0 if at least one relevant item is found, 0.0 otherwise.
    """
    recommended_item_ids = recommended_item_ids[:k]
    return 1.0 if any(item_id in true_relevance for item_id in recommended_item_ids) else 0.0

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
    3. Calculates NDCG@k, Precision@k, Recall@k, HitRate@k for each.
    4. Compares non-personalized vs. personalized results.
    5. Prints a summary report.
    6. Visualizes the results as graphs.
    """
    test_set = generate_evaluation_test_set()
    if not test_set:
        return

    results = []
    
    models_to_evaluate = ['tfidf', 'sbert', 'two_tower', 'hybrid']
    metrics = {
        'ndcg': ndcg_at_k,
        'precision': precision_at_k,
        'recall': recall_at_k,
        'hit_rate': hit_rate_at_k
    }

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
            for metric_name, metric_func in metrics.items():
                score = metric_func(ground_truth, rec_ids, k=K)
                case_results[f'{metric_name}_{model_name}'] = score

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
            for metric_name, metric_func in metrics.items():
                score = metric_func(ground_truth, rec_ids, k=K)
                case_results[f'{metric_name}_{model_name}_personalized'] = score
            
        results.append(case_results)
        
    # --- Analyze and Print Results ---
    results_df = pd.DataFrame(results)
    
    print("\n\n--- Recommender Model Evaluation Report ---")
    print(f"Based on {len(results_df)} test queries, with K={K}")
    print("--------------------------------------------------")
    
    summary = {}
    
    # Calculate average for all metrics and models (non-personalized)
    for model_name in models_to_evaluate:
        for metric_name in metrics.keys():
            col_name = f'{metric_name}_{model_name}'
            summary[f'{model_name}_{metric_name}'] = results_df[col_name].mean()
            
    # Calculate average for personalized models
    for model_name in ['sbert', 'two_tower', 'hybrid']:
        for metric_name in metrics.keys():
            col_name = f'{metric_name}_{model_name}_personalized'
            summary[f'{model_name}_personalized_{metric_name}'] = results_df[col_name].mean()
            
    summary_df = pd.DataFrame.from_dict(summary, orient='index', columns=['Average Score'])
    summary_df = summary_df.sort_values(by='Average Score', ascending=False)
    
    # Improve formatting
    summary_df['Average Score'] = summary_df['Average Score'].map('{:.4f}'.format)

    print(summary_df)
    
    print("\n\n--- Personalization Impact Analysis ---")
    print("Compares model performance with a relevant item in history vs. without.")
    
    # Create a list of dictionaries for the table
    pers_impact_data = []
    for model_name in ['sbert', 'two_tower', 'hybrid']:
        for metric_name in metrics.keys():
            base_score = summary.get(f'{model_name}_{metric_name}', 0)
            pers_score = summary.get(f'{model_name}_personalized_{metric_name}', 0)
            
            # Convert to float for calculation if they are strings
            try:
                base_score = float(base_score)
                pers_score = float(pers_score)
            except ValueError:
                base_score = 0.0
                pers_score = 0.0
                
            improvement = pers_score - base_score
            improvement_percent_str = ""
            if base_score > 0:
                improvement_percent = (improvement / base_score) * 100
                improvement_percent_str = f"{improvement_percent:+.2f}%"

            pers_impact_data.append({
                "Model": model_name.upper(),
                "Metric": metric_name.replace('_', ' ').title(),
                "Base Score": f"{base_score:.4f}",
                "Personalized Score": f"{pers_score:.4f}",
                "Change": f"{improvement:+.4f}",
                "% Change": improvement_percent_str
            })
            
    pers_impact_df = pd.DataFrame(pers_impact_data)
    print(pers_impact_df.to_string(index=False))
    print("--------------------------------------------------")

    # --- Visualize Results ---
    print("\n--- Generating Visualizations ---")
    
    # Prepare data for plotting
    plot_data = []
    for model_name in models_to_evaluate:
        for metric_name in metrics.keys():
            score = float(summary[f'{model_name}_{metric_name}'])
            plot_data.append({
                'Model': model_name.upper(),
                'Metric': metric_name.replace('_', ' ').title(),
                'Score': score,
                'Type': 'Non-Personalized'
            })
    
    for model_name in ['sbert', 'two_tower', 'hybrid']:
        for metric_name in metrics.keys():
            score = float(summary[f'{model_name}_personalized_{metric_name}'])
            plot_data.append({
                'Model': f"{model_name.upper()} (Personalized)",
                'Metric': metric_name.replace('_', ' ').title(),
                'Score': score,
                'Type': 'Personalized'
            })

    plot_df = pd.DataFrame(plot_data)

    # Bar chart for all metrics across models (Non-Personalized)
    chart1 = alt.Chart(plot_df[plot_df['Type'] == 'Non-Personalized']).mark_bar().encode(
        x=alt.X('Model:N', axis=alt.Axis(title='Model')),
        y=alt.Y('Score:Q', axis=alt.Axis(title='Average Score')),
        color='Model:N',
        column=alt.Column('Metric:N', header=alt.Header(titleOrient="bottom", labelOrient="bottom")),
        tooltip=['Model', 'Metric', alt.Tooltip('Score', format='.4f')]
    ).properties(
        title='Average Performance of Non-Personalized Models Across Metrics'
    ).resolve_scale(
        y='independent' # Independent y-axis for each facet
    )
    chart1.save('non_personalized_metrics_bar_chart.json')
    
    # Bar chart for all metrics across models (Personalized vs Non-Personalized for relevant models)
    chart2 = alt.Chart(plot_df[plot_df['Model'].isin(['SBERT', 'TWO_TOWER', 'HYBRID', 'SBERT (Personalized)', 'TWO_TOWER (Personalized)', 'HYBRID (Personalized)'])])\
        .mark_bar().encode(
        x=alt.X('Model:N', axis=alt.Axis(title='Model', labelAngle=-45)),
        y=alt.Y('Score:Q', axis=alt.Axis(title='Average Score')),
        color=alt.Color('Type:N', title='Recommendation Type'),
        column=alt.Column('Metric:N', header=alt.Header(titleOrient="bottom", labelOrient="bottom")),
        tooltip=['Model', 'Metric', 'Type', alt.Tooltip('Score', format='.4f')]
    ).properties(
        title='Average Performance: Personalized vs. Non-Personalized'
    ).resolve_scale(
        y='independent' # Independent y-axis for each facet
    )
    chart2.save('personalized_vs_non_personalized_metrics_bar_chart.json')

    print("\nVisualizations saved as 'non_personalized_metrics_bar_chart.json' and 'personalized_vs_non_personalized_metrics_bar_chart.json'.")


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