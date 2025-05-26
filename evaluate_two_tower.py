import tensorflow as tf
import numpy as np
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer
from adapted_two_tower_model import CourseRecommender
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns

def load_test_queries():
    """Load an expanded set of test queries to evaluate the model"""
    return [
        # Programming Languages
        "python data science course for beginners",
        "java programming for software development",
        "javascript full stack development",
        "c++ programming for game development",
        
        # Data Science & AI
        "machine learning with tensorflow",
        "deep learning for computer vision",
        "natural language processing with python",
        "data analysis with pandas and numpy",
        
        # Web Development
        "web development with react and node.js",
        "full stack development with django",
        "frontend development with angular",
        "backend development with spring boot",
        
        # Cloud & DevOps
        "cloud computing with aws",
        "devops and continuous integration",
        "kubernetes and container orchestration",
        "microservices architecture",
        
        # Mobile Development
        "mobile app development with flutter",
        "ios development with swift",
        "android development with kotlin",
        "cross platform mobile development",
        
        # Database
        "sql database design and optimization",
        "nosql databases with mongodb",
        "data warehousing and etl",
        "database administration",
        
        # Security
        "cybersecurity fundamentals",
        "ethical hacking and penetration testing",
        "network security and protocols",
        "cloud security best practices"
    ]

def evaluate_recommendations(recommender, query, top_k=5):
    """Evaluate recommendations for a single query with enhanced metrics"""
    # Get recommendations from both models
    two_tower_recs = recommender.recommend(query, top_k=top_k)
    sbert_recs = recommender.get_sbert_recommendations(query, top_k=top_k)
    
    # Calculate overlap metrics
    two_tower_titles = set(two_tower_recs['title'].tolist())
    sbert_titles = set(sbert_recs['title'].tolist())
    overlap = len(two_tower_titles.intersection(sbert_titles))
    overlap_ratio = overlap / top_k
    
    # Calculate average similarity scores
    two_tower_avg_score = two_tower_recs['similarity_score'].mean()
    sbert_avg_score = sbert_recs['sbert_similarity_score'].mean()
    
    # Calculate provider diversity
    two_tower_providers = len(set(two_tower_recs['provider'].tolist()))
    sbert_providers = len(set(sbert_recs['provider'].tolist()))
    
    # Calculate level diversity
    two_tower_levels = len(set(two_tower_recs['level'].tolist())) if 'level' in two_tower_recs.columns else 0
    sbert_levels = len(set(sbert_recs['level'].tolist())) if 'level' in sbert_recs.columns else 0
    
    return {
        'query': query,
        'two_tower_recs': two_tower_recs,
        'sbert_recs': sbert_recs,
        'overlap': overlap,
        'overlap_ratio': overlap_ratio,
        'two_tower_avg_score': two_tower_avg_score,
        'sbert_avg_score': sbert_avg_score,
        'two_tower_provider_diversity': two_tower_providers,
        'sbert_provider_diversity': sbert_providers,
        'two_tower_level_diversity': two_tower_levels,
        'sbert_level_diversity': sbert_levels
    }

def plot_evaluation_metrics(results):
    """Plot various evaluation metrics"""
    # Prepare data for plotting
    metrics_df = pd.DataFrame([
        {
            'query': r['query'],
            'overlap_ratio': r['overlap_ratio'],
            'two_tower_score': r['two_tower_avg_score'],
            'sbert_score': r['sbert_avg_score'],
            'two_tower_providers': r['two_tower_provider_diversity'],
            'sbert_providers': r['sbert_provider_diversity']
        }
        for r in results
    ])
    
    # Create plots
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Overlap Ratio Distribution
    plt.subplot(2, 2, 1)
    sns.histplot(data=metrics_df, x='overlap_ratio', bins=10)
    plt.title('Distribution of Overlap Ratios')
    plt.xlabel('Overlap Ratio')
    
    # Plot 2: Average Similarity Scores
    plt.subplot(2, 2, 2)
    sns.boxplot(data=metrics_df[['two_tower_score', 'sbert_score']])
    plt.title('Average Similarity Scores')
    plt.xticks([0, 1], ['Two-Tower', 'SBERT'])
    
    # Plot 3: Provider Diversity
    plt.subplot(2, 2, 3)
    sns.boxplot(data=metrics_df[['two_tower_providers', 'sbert_providers']])
    plt.title('Provider Diversity')
    plt.xticks([0, 1], ['Two-Tower', 'SBERT'])
    
    # Save the plot
    plt.tight_layout()
    plt.savefig('evaluation_metrics.png')
    plt.close()

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
        
        # Print detailed results for this query
        print(f"Overlap with SBERT: {result['overlap']}/5 courses ({result['overlap_ratio']:.2%})")
        print(f"Two-Tower Avg Score: {result['two_tower_avg_score']:.4f}")
        print(f"SBERT Avg Score: {result['sbert_avg_score']:.4f}")
        print(f"Two-Tower Provider Diversity: {result['two_tower_provider_diversity']}")
        print(f"SBERT Provider Diversity: {result['sbert_provider_diversity']}")
        
        print("\nTwo-Tower Recommendations:")
        print(result['two_tower_recs'][['title', 'provider', 'similarity_score']].to_string())
        print("\nSBERT Recommendations:")
        print(result['sbert_recs'][['title', 'provider', 'sbert_similarity_score']].to_string())
    
    # Calculate and print overall metrics
    avg_overlap = np.mean([r['overlap_ratio'] for r in results])
    avg_two_tower_score = np.mean([r['two_tower_avg_score'] for r in results])
    avg_sbert_score = np.mean([r['sbert_avg_score'] for r in results])
    avg_two_tower_providers = np.mean([r['two_tower_provider_diversity'] for r in results])
    avg_sbert_providers = np.mean([r['sbert_provider_diversity'] for r in results])
    
    print("\nOverall Evaluation Metrics:")
    print(f"Average overlap ratio: {avg_overlap:.2%}")
    print(f"Average Two-Tower similarity score: {avg_two_tower_score:.4f}")
    print(f"Average SBERT similarity score: {avg_sbert_score:.4f}")
    print(f"Average Two-Tower provider diversity: {avg_two_tower_providers:.2f}")
    print(f"Average SBERT provider diversity: {avg_sbert_providers:.2f}")
    
    # Generate plots
    print("\nGenerating evaluation plots...")
    plot_evaluation_metrics(results)
    
    # Save detailed results
    results_df = pd.DataFrame([
        {
            'query': r['query'],
            'overlap': r['overlap'],
            'overlap_ratio': r['overlap_ratio'],
            'two_tower_avg_score': r['two_tower_avg_score'],
            'sbert_avg_score': r['sbert_avg_score'],
            'two_tower_provider_diversity': r['two_tower_provider_diversity'],
            'sbert_provider_diversity': r['sbert_provider_diversity'],
            'two_tower_level_diversity': r['two_tower_level_diversity'],
            'sbert_level_diversity': r['sbert_level_diversity']
        }
        for r in results
    ])
    results_df.to_csv('two_tower_evaluation_results.csv', index=False)
    print("\nDetailed results saved to 'two_tower_evaluation_results.csv'")
    print("Evaluation plots saved to 'evaluation_metrics.png'")

if __name__ == "__main__":
    main() 