import pandas as pd
import numpy as np
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import warnings
import matplotlib.pyplot as plt # For plotting
import seaborn as sns          # For better-looking plots
import torch 
from sentence_transformers import SentenceTransformer, util
import pickle 
import os 
import sys 

# --- Suppress specific warnings for cleaner output ---
warnings.filterwarnings("ignore", category=UserWarning, module='tensorflow')
warnings.filterwarnings("ignore", category=UserWarning, module='sklearn')

# --- Import components from the main recommender system ---
try:
    from recommender_interface_advanced_v6 import (
        get_recommendations,
        df_all_courses,
        tfidf_vectorizer,
        tfidf_matrix,
        preprocess_text_for_tfidf,
    )
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"FATAL: Could not import necessary components from recommender_interface_advanced_v6.py. Error: {e}")
    print("Please ensure 'recommender_interface_advanced_v6.py' is in the same directory and all its dependencies are installed.")
    IMPORTS_SUCCESSFUL = False

# --- Configuration ---
K = 10  
TEST_SET_SIZE = 50  
TFIDF_SIMILARITY_THRESHOLD = 0.3
SBERT_SIMILARITY_THRESHOLD = 0.5

# --- Loading SBERT model and embeddings for ground truth generation ---
sbert_model_for_gt = None
course_sbert_embeddings_for_gt = None
course_sbert_ids_for_gt = None

if IMPORTS_SUCCESSFUL:
    try:
        # This assumes a 'config.py' file is available in the parent directory
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        PARENT_DIR = os.path.dirname(SCRIPT_DIR)
        if PARENT_DIR not in sys.path:
            sys.path.append(PARENT_DIR)
        
        import config 

        device = "cuda" if torch.cuda.is_available() else "cpu"
        sbert_model_for_gt = SentenceTransformer(config.SBERT_MODEL_NAME, device=device)
        print(f"SBERT model '{config.SBERT_MODEL_NAME}' loaded for ground truth generation on {device}.")

        if os.path.exists(config.SBERT_EMBEDDINGS_PATH) and os.path.exists(config.SBERT_COURSE_IDS_PATH):
            with open(config.SBERT_EMBEDDINGS_PATH, 'rb') as f:
                course_sbert_embeddings_for_gt = pickle.load(f)
            with open(config.SBERT_COURSE_IDS_PATH, 'rb') as f:
                course_sbert_ids_for_gt = pickle.load(f)
            print(f"Loaded course SBERT embeddings and IDs.")
            
            if len(course_sbert_embeddings_for_gt) != len(course_sbert_ids_for_gt):
                print("Warning: SBERT embeddings and IDs length mismatch. Disabling SBERT for ground truth.")
                sbert_model_for_gt = None 
        else:
            print(f"Warning: SBERT embeddings or IDs not found. SBERT ground truth will not be used.")
            sbert_model_for_gt = None
            
    except Exception as e:
        print(f"Error loading SBERT model or embeddings for ground truth: {e}")
        sbert_model_for_gt = None

# --- Evaluation Metrics ---
def ndcg_at_k(true_relevance, recommended_item_ids, k=K):
    recommended_item_ids = recommended_item_ids[:k]
    dcg = sum(1 / np.log2(i + 2) for i, item_id in enumerate(recommended_item_ids) if item_id in true_relevance)
    ideal_k = min(k, len(true_relevance))
    idcg = sum(1 / np.log2(i + 2) for i in range(ideal_k))
    return dcg / idcg if idcg > 0 else 0.0

def precision_at_k(true_relevance, recommended_item_ids, k=K):
    recommended_item_ids = recommended_item_ids[:k]
    num_hits = sum(1 for item_id in recommended_item_ids if item_id in true_relevance)
    return num_hits / k if k > 0 else 0.0

def recall_at_k(true_relevance, recommended_item_ids, k=K):
    recommended_item_ids = recommended_item_ids[:k]
    num_hits = sum(1 for item_id in recommended_item_ids if item_id in true_relevance)
    return num_hits / len(true_relevance) if len(true_relevance) > 0 else 0.0

def hit_rate_at_k(true_relevance, recommended_item_ids, k=K):
    recommended_item_ids = recommended_item_ids[:k]
    return 1.0 if any(item_id in true_relevance for item_id in recommended_item_ids) else 0.0

# --- Test Set Generation ---
def generate_evaluation_test_set(size=TEST_SET_SIZE):
    if df_all_courses is None or tfidf_matrix is None:
        print("Cannot generate test set. Course data or TF-IDF matrix not loaded.")
        return []
    
    use_sbert_for_gt = sbert_model_for_gt is not None

    test_set = []
    print(f"\n--- Generating evaluation test set of size {size}... ---")
    
    sample_size = min(size, len(df_all_courses))
    sample_courses = df_all_courses.sample(n=sample_size, random_state=42)

    for idx, row in tqdm(sample_courses.iterrows(), total=sample_size, desc="Building Test Set"):
        query_text, query_item_id = row['title'], row['item_id']
        
        query_vector_tfidf = tfidf_vectorizer.transform([preprocess_text_for_tfidf(query_text)])
        similarities_tfidf = cosine_similarity(query_vector_tfidf, tfidf_matrix).flatten()
        relevant_indices_tfidf = np.where(similarities_tfidf > TFIDF_SIMILARITY_THRESHOLD)[0]
        ground_truth_ids_tfidf = set(df_all_courses.iloc[relevant_indices_tfidf]['item_id'])
        
        ground_truth_ids_sbert = set()
        if use_sbert_for_gt:
            try:
                query_embedding_sbert = sbert_model_for_gt.encode(query_text, convert_to_tensor=True)
                sbert_embeddings_tensor = torch.tensor(course_sbert_embeddings_for_gt, dtype=torch.float32)
                similarities_sbert = util.cos_sim(query_embedding_sbert, sbert_embeddings_tensor).cpu().numpy().flatten()
                
                sbert_df = pd.DataFrame({'item_id': course_sbert_ids_for_gt, 'similarity': similarities_sbert})
                relevant_sbert_items = sbert_df[sbert_df['similarity'] > SBERT_SIMILARITY_THRESHOLD]
                ground_truth_ids_sbert = set(relevant_sbert_items['item_id'])
            except Exception as e:
                print(f"Error during SBERT ground truth generation: {e}")
        
        combined_ground_truth_ids = ground_truth_ids_tfidf.union(ground_truth_ids_sbert)
        combined_ground_truth_ids.discard(query_item_id)
        
        if not combined_ground_truth_ids: continue
            
        history_item = np.random.choice(list(combined_ground_truth_ids))
        test_set.append({"query_text": query_text, "ground_truth": combined_ground_truth_ids, "history_item": history_item})
        
    print(f"--- Successfully generated a test set with {len(test_set)} valid queries. ---")
    return test_set

# --- Organized Reporting Function ---
def print_organized_report(results_df, models_to_evaluate, metrics):
    print("\n" + "="*80)
    print(" " * 25 + "Recommender Model Evaluation Report")
    print("="*80)
    print(f"Based on {len(results_df)} test queries with K={K}\n")

    non_pers_data, pers_data = [], []
    for model in models_to_evaluate:
        row_non_pers, row_pers = {'Model': model.upper()}, {'Model': f'{model.upper()} (Personalized)'}
        for metric in metrics:
            metric_title = metric.replace("_", " ").title()
            row_non_pers[metric_title] = results_df[f'{metric}_{model}'].mean()
            row_pers[metric_title] = results_df[f'{metric}_{model}_personalized'].mean()
        non_pers_data.append(row_non_pers)
        pers_data.append(row_pers)
    
    non_pers_df = pd.DataFrame(non_pers_data).set_index('Model')
    pers_df = pd.DataFrame(pers_data).set_index('Model')

    print("--- 1. Average Performance of Non-Personalized Models ---")
    print(non_pers_df.to_string(float_format="{:.4f}".format))
    print("\n" + "-"*80 + "\n")
    print("--- 2. Average Performance of Personalized Models ---")
    print(pers_df.to_string(float_format="{:.4f}".format))
    print("\n" + "-"*80 + "\n")
    print("--- 3. Personalization Impact Analysis ---")
    print("Compares model performance with a relevant item in history vs. without.\n")

    impact_data = []
    for model in models_to_evaluate:
        for metric in metrics:
            metric_title = metric.replace('_', ' ').title()
            base_score = non_pers_df.loc[model.upper(), metric_title]
            pers_score = pers_df.loc[f'{model.upper()} (Personalized)', metric_title]
            improvement = pers_score - base_score
            improvement_percent_str = f"{(improvement / base_score) * 100:+.2f}%" if base_score > 0 else "N/A"
            impact_data.append({
                "Model": model.upper(), "Metric": metric_title, "Base Score": f"{base_score:.4f}",
                "Personalized Score": f"{pers_score:.4f}", "Change": f"{improvement:+.4f}",
                "% Change": improvement_percent_str
            })
    print(pd.DataFrame(impact_data).to_string(index=False))
    print("\n" + "="*80)

def evaluate_models():
    if not IMPORTS_SUCCESSFUL: return
    test_set = generate_evaluation_test_set()
    if not test_set: return

    results = []
    models_to_evaluate = ['tfidf', 'sbert', 'two_tower', 'hybrid']
    metrics = ['ndcg', 'precision', 'recall', 'hit_rate']
    metric_funcs = {'ndcg': ndcg_at_k, 'precision': precision_at_k, 'recall': recall_at_k, 'hit_rate': hit_rate_at_k}

    for test_case in tqdm(test_set, desc="Evaluating All Models"):
        query_text, ground_truth, history_item = test_case.values()
        case_results = {'query': query_text}

        for model_name in models_to_evaluate:
            recs = get_recommendations(query_text=query_text, top_n=K, model_type=model_name)
            rec_ids = recs['item_id'].tolist() if not recs.empty else []
            recs_pers = get_recommendations(query_text=query_text, user_history=[history_item], top_n=K, model_type=model_name)
            rec_ids_pers = recs_pers['item_id'].tolist() if not recs_pers.empty else []

            for metric_name, metric_func in metric_funcs.items():
                case_results[f'{metric_name}_{model_name}'] = metric_func(ground_truth, rec_ids, k=K)
                case_results[f'{metric_name}_{model_name}_personalized'] = metric_func(ground_truth, rec_ids_pers, k=K)
        results.append(case_results)
        
    results_df = pd.DataFrame(results)
    print_organized_report(results_df, models_to_evaluate, metrics)

    # --- Start of Visualization Code for Non-Personalized Models ---
    print("\n--- Generating Visualizations for Non-Personalized Models ---")

    # Data Preparation for Non-Personalized Plotting
    plot_data_non_pers = []
    for model in models_to_evaluate:
        for metric in metrics:
            metric_title = metric.replace('_', ' ').title()
            plot_data_non_pers.append({
                'Model': model.upper(),
                'Metric': metric_title,
                'Score': results_df[f'{metric}_{model}'].mean()
            })
    plot_df_non_pers = pd.DataFrame(plot_data_non_pers)

    sns.set_theme(style="whitegrid")

    # Chart 1: Average Performance of Non-Personalized Models (Catplot)
    print("\n--- Non-Personalized Chart 1: Average Performance (by Metric) ---")
    g1_non_pers = sns.catplot(
        data=plot_df_non_pers, x='Model', y='Score', col='Metric',
        kind='bar', col_wrap=2, sharey=False,
        height=5, aspect=1.2,
        hue='Model', legend=False
    )
    g1_non_pers.fig.suptitle('Average Performance of Non-Personalized Models', y=1.03, fontsize=16)
    g1_non_pers.set_axis_labels("Model", "Average Score")
    g1_non_pers.set_titles("Metric: {col_name}")
    for ax in g1_non_pers.axes.flat:
        if ax.get_xticklabels():
            ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right')
    plt.subplots_adjust(bottom=0.25, hspace=0.4, wspace=0.3)
    plt.savefig('non_personalized_metrics_by_metric.png', bbox_inches='tight')
    print("Non-Personalized Chart 1 saved as 'non_personalized_metrics_by_metric.png'.")
    plt.close(g1_non_pers.fig)

    # Chart 2: Comparison of Non-Personalized Models Across Metrics (Grouped Bar Plot)
    print("\n--- Non-Personalized Chart 2: Comparison Across Metrics ---")
    plt.figure(figsize=(12, 7))
    sns.barplot(
        data=plot_df_non_pers, x='Metric', y='Score', hue='Model',
        palette='viridis'
    )
    plt.title('Comparison of Non-Personalized Models Across Metrics', fontsize=16)
    plt.xlabel("Metric", fontsize=12)
    plt.ylabel("Average Score", fontsize=12)
    plt.xticks(rotation=30, ha='right')
    plt.legend(title='Model', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('non_personalized_metrics_grouped_bar.png', bbox_inches='tight')
    print("Non-Personalized Chart 2 saved as 'non_personalized_metrics_grouped_bar.png'.")
    plt.close()

    # Additional Chart: Heatmap of Non-Personalized Performance
    print("\n--- Non-Personalized Additional Chart: Heatmap ---")
    heatmap_data_non_pers = plot_df_non_pers.pivot_table(index='Metric', columns='Model', values='Score')
    plt.figure(figsize=(10, 7))
    sns.heatmap(
        heatmap_data_non_pers, annot=True, cmap='Blues', fmt=".3f", linewidths=.5,
        cbar_kws={'label': 'Average Score'}
    )
    plt.title('Heatmap of Non-Personalized Model Performance', fontsize=16)
    plt.xlabel('Model', fontsize=12)
    plt.ylabel('Metric', fontsize=12)
    plt.tight_layout()
    plt.savefig('non_personalized_metrics_heatmap.png', bbox_inches='tight')
    print("Non-Personalized Additional Chart saved as 'non_personalized_metrics_heatmap.png'.")
    plt.close()

    print("\n--- Generating Visualizations for Personalized Models ---")

    # Data Preparation for Personalized Plotting
    plot_data_pers = []
    for model in models_to_evaluate:
        for metric in metrics:
            metric_title = metric.replace('_', ' ').title()
            plot_data_pers.append({
                'Model': model.upper(),
                'Metric': metric_title,
                'Score': results_df[f'{metric}_{model}_personalized'].mean() # Use personalized scores
            })
    plot_df_pers = pd.DataFrame(plot_data_pers)

    # Chart 4: Average Performance of Personalized Models (Catplot)
    print("\n--- Personalized Chart 1: Average Performance (by Metric) ---")
    g1_pers = sns.catplot(
        data=plot_df_pers, x='Model', y='Score', col='Metric',
        kind='bar', col_wrap=2, sharey=False,
        height=5, aspect=1.2,
        hue='Model', legend=False
    )
    g1_pers.fig.suptitle('Average Performance of Personalized Models', y=1.03, fontsize=16)
    g1_pers.set_axis_labels("Model", "Average Score")
    g1_pers.set_titles("Metric: {col_name}")
    for ax in g1_pers.axes.flat:
        if ax.get_xticklabels():
            ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right')
    plt.subplots_adjust(bottom=0.25, hspace=0.4, wspace=0.3)
    plt.savefig('personalized_metrics_by_metric.png', bbox_inches='tight')
    print("Personalized Chart 1 saved as 'personalized_metrics_by_metric.png'.")
    plt.close(g1_pers.fig)

    # Chart 5: Comparison of Personalized Models Across Metrics (Grouped Bar Plot)
    print("\n--- Personalized Chart 2: Comparison Across Metrics ---")
    plt.figure(figsize=(12, 7))
    sns.barplot(
        data=plot_df_pers, x='Metric', y='Score', hue='Model',
        palette='viridis'
    )
    plt.title('Comparison of Personalized Models Across Metrics', fontsize=16)
    plt.xlabel("Metric", fontsize=12)
    plt.ylabel("Average Score", fontsize=12)
    plt.xticks(rotation=30, ha='right')
    plt.legend(title='Model', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('personalized_metrics_grouped_bar.png', bbox_inches='tight')
    print("Personalized Chart 2 saved as 'personalized_metrics_grouped_bar.png'.")
    plt.close()

    # Additional Chart: Heatmap of Personalized Performance
    print("\n--- Personalized Additional Chart: Heatmap ---")
    heatmap_data_pers = plot_df_pers.pivot_table(index='Metric', columns='Model', values='Score')
    plt.figure(figsize=(10, 7))
    sns.heatmap(
        heatmap_data_pers, annot=True, cmap='Blues', fmt=".3f", linewidths=.5,
        cbar_kws={'label': 'Average Score'}
    )
    plt.title('Heatmap of Personalized Model Performance', fontsize=16)
    plt.xlabel('Model', fontsize=12)
    plt.ylabel('Metric', fontsize=12)
    plt.tight_layout()
    plt.savefig('personalized_metrics_heatmap.png', bbox_inches='tight')
    print("Personalized Additional Chart saved as 'personalized_metrics_heatmap.png'.")
    plt.close()

    print("\nAll requested visualizations generated and saved.")
    # --- End of Visualization Code ---

if __name__ == "__main__":
    if IMPORTS_SUCCESSFUL:
        print("Starting the model evaluation script...")
        if df_all_courses is not None and tfidf_vectorizer is not None:
            evaluate_models()
        else:
            print("\nFATAL: Cannot run evaluation because course data or TF-IDF models failed to load.")
    else:
        print("\nEvaluation script cannot run due to import failures.")
