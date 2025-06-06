import pandas as pd
import numpy as np
from recommender_interface_advanced_v6 import get_hybrid_recommendations_advanced
from sklearn.model_selection import KFold

# --- Configuration ---
TEST_QUERIES = [
    "learn machine learning with python",
    "data science for beginners",
    "advanced deep learning",
    "web development with javascript",
    "anatomical terminology"
]

GROUND_TRUTH = {
    "learn machine learning with python": ["Machine Learning A-Z", "Python for Data Science"],
    "data science for beginners": ["Data Science Bootcamp", "Introduction to Data Science"],
    "advanced deep learning": ["Deep Learning Specialization", "Advanced Neural Networks"],
    "web development with javascript": ["Full Stack Web Development", "JavaScript Masterclass"],
    "anatomical terminology": ["Anatomy and Physiology", "Medical Terminology"]
}

# --- Evaluation Metrics ---
def precision_at_k(recommended, ground_truth, k):
    """Calculate precision@k."""
    recommended_k = recommended[:k]
    hits = sum(1 for item in recommended_k if item in ground_truth)
    return hits / k if k > 0 else 0

def recall_at_k(recommended, ground_truth, k):
    """Calculate recall@k."""
    recommended_k = recommended[:k]
    hits = sum(1 for item in recommended_k if item in ground_truth)
    return hits / len(ground_truth) if ground_truth else 0

def mean_reciprocal_rank(recommended, ground_truth):
    """Calculate Mean Reciprocal Rank (MRR)."""
    for i, item in enumerate(recommended):
        if item in ground_truth:
            return 1 / (i + 1)
    return 0

def ndcg_at_k(recommended, ground_truth, k):
    """Calculate Normalized Discounted Cumulative Gain (NDCG)@k."""
    dcg = 0
    idcg = sum(1 / np.log2(i + 2) for i in range(min(len(ground_truth), k)))
    for i, item in enumerate(recommended[:k]):
        if item in ground_truth:
            dcg += 1 / np.log2(i + 2)
    return dcg / idcg if idcg > 0 else 0

def mean_average_precision(recommended, ground_truth):
    """Calculate Mean Average Precision (MAP)."""
    ap = 0
    hits = 0
    for i, item in enumerate(recommended):
        if item in ground_truth:
            hits += 1
            ap += hits / (i + 1)
    return ap / len(ground_truth) if ground_truth else 0

def evaluate_model(model_type, k=4):
    """Evaluate a model using precision@k, recall@k, MRR, NDCG@k, and MAP."""
    results = []
    for query in TEST_QUERIES:
        recommendations = get_hybrid_recommendations_advanced(query_text=query, model_type=model_type, top_n=k)
        recommended_titles = recommendations['title'].tolist()
        ground_truth_titles = GROUND_TRUTH[query]
        precision = precision_at_k(recommended_titles, ground_truth_titles, k)
        recall = recall_at_k(recommended_titles, ground_truth_titles, k)
        mrr = mean_reciprocal_rank(recommended_titles, ground_truth_titles)
        ndcg = ndcg_at_k(recommended_titles, ground_truth_titles, k)
        map_score = mean_average_precision(recommended_titles, ground_truth_titles)
        results.append({
            'query': query,
            'precision@k': precision,
            'recall@k': recall,
            'mrr': mrr,
            'ndcg@k': ndcg,
            'map': map_score
        })
    return pd.DataFrame(results)

# --- Cross-Validation ---
def cross_validate_model(model_type, k=4, n_splits=5):
    """Perform cross-validation on the model."""
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    all_results = []
    for train_idx, test_idx in kf.split(TEST_QUERIES):
        train_queries = [TEST_QUERIES[i] for i in train_idx]
        test_queries = [TEST_QUERIES[i] for i in test_idx]
        # Evaluate on test queries
        results = evaluate_model(model_type, k)
        all_results.append(results)
    return pd.concat(all_results).groupby('query').mean()

# --- Main Evaluation ---
if __name__ == "__main__":
    print("Evaluating TF-IDF model...")
    tfidf_results = evaluate_model("tfidf")
    print(tfidf_results)

    print("\nEvaluating SBERT model...")
    sbert_results = evaluate_model("sbert")
    print(sbert_results)

    print("\nEvaluating Two-Tower model...")
    two_tower_results = evaluate_model("two_tower")
    print(two_tower_results)

    print("\nEvaluating Hybrid model...")
    hybrid_results = evaluate_model("hybrid_tfidf_sbert")
    print(hybrid_results)

    print("\nCross-validating Hybrid model...")
    cv_results = cross_validate_model("hybrid_tfidf_sbert")
    print(cv_results)

    print("\nEvaluation complete.") 