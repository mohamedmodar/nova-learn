import tensorflow as tf
import numpy as np
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer
from adapted_two_tower_model import CourseRecommender
from sklearn.metrics.pairwise import cosine_similarity

def load_test_queries():
    """Load a set of test queries to evaluate the model"""
    return [
        "python data science course for beginners",
        "machine learning with tensorflow",
        "web development with react and node.js",
        "data structures and algorithms in java",
        "deep learning for computer vision",
        "sql database design and optimization",
        "cloud computing with aws",
        "mobile app development with flutter",
        "cybersecurity fundamentals",
        "devops and continuous integration"
    ]

def evaluate_recommendations(recommender, query, top_k=5):
    """Evaluate recommendations for a single query"""
    # Get recommendations from both models
    two_tower_recs = recommender.recommend(query, top_k=top_k)
    
    # Get raw SBERT recommendations for comparison
    sbert_recs = recommender.get_sbert_recommendations(query, top_k=top_k)
    
    # Compare the recommendations
    two_tower_titles = set(two_tower_recs['title'].tolist())
    sbert_titles = set(sbert_recs['title'].tolist())
    
    # Calculate overlap
    overlap = len(two_tower_titles.intersection(sbert_titles))
    overlap_ratio = overlap / top_k
    
    return {
        'query': query,
        'two_tower_recs': two_tower_recs,
        'sbert_recs': sbert_recs,
        'overlap': overlap,
        'overlap_ratio': overlap_ratio
    }

def main():
    print("Loading trained Two-Tower model...")
    recommender = CourseRecommender(model_path='two_tower.weights.h5')
    
    print("\nLoading test queries...")
    test_queries = load_test_queries()
    
    print("\nEvaluating recommendations...")
    results = []
    for query in test_queries:
        print(f"\nEvaluating query: {query}")
        result = evaluate_recommendations(recommender, query)
        results.append(result)
        
        # Print results for this query
        print(f"Overlap with SBERT: {result['overlap']}/5 courses ({result['overlap_ratio']:.2%})")
        print("\nTwo-Tower Recommendations:")
        print(result['two_tower_recs'][['title', 'provider', 'similarity_score']].to_string())
        print("\nSBERT Recommendations:")
        print(result['sbert_recs'][['title', 'provider', 'sbert_similarity_score']].to_string())
    
    # Calculate average metrics
    avg_overlap = np.mean([r['overlap_ratio'] for r in results])
    print(f"\nAverage overlap ratio: {avg_overlap:.2%}")
    
    # Save detailed results
    results_df = pd.DataFrame([
        {
            'query': r['query'],
            'overlap': r['overlap'],
            'overlap_ratio': r['overlap_ratio']
        }
        for r in results
    ])
    results_df.to_csv('two_tower_evaluation_results.csv', index=False)
    print("\nDetailed results saved to 'two_tower_evaluation_results.csv'")

if __name__ == "__main__":
    main() 