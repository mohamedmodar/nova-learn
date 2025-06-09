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

def evaluate_recommendations(recommender, query):
    """Evaluate recommendations for a given query using both models."""
    # Get recommendations from both models
    two_tower_recs = recommender.recommend(query_text=query, top_k=5)
    sbert_recs = recommender.get_sbert_recommendations(query_text=query, top_k=5)
    
    if two_tower_recs.empty or sbert_recs.empty:
        print(f"Warning: No recommendations generated for query: {query}")
        return None
    
    # Calculate similarity score statistics
    two_tower_sim_mean = two_tower_recs['similarity_score'].mean()
    two_tower_sim_std = two_tower_recs['similarity_score'].std()
    sbert_sim_mean = sbert_recs['sbert_similarity_score'].mean()
    sbert_sim_std = sbert_recs['sbert_similarity_score'].std()
    
    # Calculate rating statistics
    two_tower_rating_mean = two_tower_recs['adjusted_rating'].mean()
    two_tower_rating_std = two_tower_recs['adjusted_rating'].std()
    sbert_rating_mean = sbert_recs['adjusted_rating'].mean()
    sbert_rating_std = sbert_recs['adjusted_rating'].std()
    
    # Calculate overlap between recommendations
    two_tower_titles = set(two_tower_recs['title'])
    sbert_titles = set(sbert_recs['title'])
    overlap = len(two_tower_titles.intersection(sbert_titles))
    overlap_ratio = overlap / len(two_tower_titles.union(sbert_titles)) if two_tower_titles.union(sbert_titles) else 0
    
    # Calculate skill diversity (if skills_list column exists)
    two_tower_skills = set()
    sbert_skills = set()
    
    if 'skills_list' in two_tower_recs.columns:
        for skills in two_tower_recs['skills_list']:
            if isinstance(skills, list):
                two_tower_skills.update(skills)
    
    if 'skills_list' in sbert_recs.columns:
        for skills in sbert_recs['skills_list']:
            if isinstance(skills, list):
                sbert_skills.update(skills)
    
    two_tower_skill_diversity = len(two_tower_skills)
    sbert_skill_diversity = len(sbert_skills)
    
    return {
        'query': query,
        'two_tower_sim_mean': two_tower_sim_mean,
        'two_tower_sim_std': two_tower_sim_std,
        'sbert_sim_mean': sbert_sim_mean,
        'sbert_sim_std': sbert_sim_std,
        'two_tower_rating_mean': two_tower_rating_mean,
        'two_tower_rating_std': two_tower_rating_std,
        'sbert_rating_mean': sbert_rating_mean,
        'sbert_rating_std': sbert_rating_std,
        'overlap': overlap,
        'overlap_ratio': overlap_ratio,
        'two_tower_skill_diversity': two_tower_skill_diversity,
        'sbert_skill_diversity': sbert_skill_diversity,
        'two_tower_recs': two_tower_recs,
        'sbert_recs': sbert_recs
    }

def plot_evaluation_metrics(results):
    """Plot various evaluation metrics"""
    # Prepare data for plotting
    metrics_df = pd.DataFrame([
        {
            'query': r['query'],
            'two_tower_sim': r['two_tower_sim_mean'],
            'sbert_sim': r['sbert_sim_mean'],
            'two_tower_rating': r['two_tower_rating_mean'],
            'sbert_rating': r['sbert_rating_mean'],
            'overlap': r['overlap'],
            'overlap_ratio': r['overlap_ratio'],
            'two_tower_skills': r['two_tower_skill_diversity'],
            'sbert_skills': r['sbert_skill_diversity']
        }
        for r in results
    ])
    
    # Create plots
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Similarity Scores
    plt.subplot(2, 2, 1)
    sns.boxplot(data=metrics_df[['two_tower_sim', 'sbert_sim']])
    plt.title('Similarity Scores')
    
    # Plot 2: Ratings
    plt.subplot(2, 2, 2)
    sns.boxplot(data=metrics_df[['two_tower_rating', 'sbert_rating']])
    plt.title('Ratings')
    
    # Plot 3: Skill Diversity
    plt.subplot(2, 2, 3)
    sns.boxplot(data=metrics_df[['two_tower_skills', 'sbert_skills']])
    plt.title('Skill Diversity')
    
    # Plot 4: Overlap Ratio
    plt.subplot(2, 2, 4)
    sns.histplot(metrics_df['overlap_ratio'], bins=10)
    plt.title('Recommendation Overlap Ratio')
    
    plt.tight_layout()
    plt.savefig('evaluation_results.png')
    plt.close()

def main():
    print("Loading trained Two-Tower model...")
    recommender = CourseRecommender(model_path='models/two_tower_model.weights.h5')
    
    print("\nLoading test queries...")
    test_queries = load_test_queries()
    
    print("\nEvaluating recommendations...")
    results = []
    for query in test_queries:
        print(f"\nEvaluating query: {query}")
        result = evaluate_recommendations(recommender, query)
        if result:
            results.append(result)
        
        # Print detailed results for this query
        print(f"Overlap with SBERT: {result['overlap']}/5 courses ({result['overlap_ratio']:.2%})")
        print(f"Two-Tower Avg Similarity: {result['two_tower_sim_mean']:.4f} ± {result['two_tower_sim_std']:.4f}")
        print(f"SBERT Avg Similarity: {result['sbert_sim_mean']:.4f} ± {result['sbert_sim_std']:.4f}")
        print(f"Two-Tower Avg Rating: {result['two_tower_rating_mean']:.2f} ± {result['two_tower_rating_std']:.2f}")
        print(f"SBERT Avg Rating: {result['sbert_rating_mean']:.2f} ± {result['sbert_rating_std']:.2f}")
        print(f"Two-Tower Skill Diversity: {result['two_tower_skill_diversity']}")
        print(f"SBERT Skill Diversity: {result['sbert_skill_diversity']}")
        
        print("\nTwo-Tower Recommendations:")
        print(result['two_tower_recs'][['title', 'similarity_score', 'adjusted_rating']].to_string())
        print("\nSBERT Recommendations:")
        print(result['sbert_recs'][['title', 'sbert_similarity_score', 'adjusted_rating']].to_string())
    
    if not results:
        print("No valid results to analyze.")
        return
    
    # Convert results to DataFrame for analysis
    metrics_df = pd.DataFrame([{
        'query': r['query'],
        'two_tower_sim': r['two_tower_sim_mean'],
        'sbert_sim': r['sbert_sim_mean'],
        'two_tower_rating': r['two_tower_rating_mean'],
        'sbert_rating': r['sbert_rating_mean'],
        'overlap': r['overlap'],
        'overlap_ratio': r['overlap_ratio'],
        'two_tower_skills': r['two_tower_skill_diversity'],
        'sbert_skills': r['sbert_skill_diversity']
    } for r in results])
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(metrics_df.describe())
    
    # Create visualizations
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Similarity Scores
    plt.subplot(2, 2, 1)
    sns.boxplot(data=metrics_df[['two_tower_sim', 'sbert_sim']])
    plt.title('Similarity Scores')
    
    # Plot 2: Ratings
    plt.subplot(2, 2, 2)
    sns.boxplot(data=metrics_df[['two_tower_rating', 'sbert_rating']])
    plt.title('Ratings')
    
    # Plot 3: Skill Diversity
    plt.subplot(2, 2, 3)
    sns.boxplot(data=metrics_df[['two_tower_skills', 'sbert_skills']])
    plt.title('Skill Diversity')
    
    # Plot 4: Overlap Ratio
    plt.subplot(2, 2, 4)
    sns.histplot(metrics_df['overlap_ratio'], bins=10)
    plt.title('Recommendation Overlap Ratio')
    
    plt.tight_layout()
    plt.savefig('evaluation_results.png')
    plt.close()
    
    # Calculate and print average metrics
    avg_two_tower_sim = np.mean([r['two_tower_sim_mean'] for r in results])
    avg_sbert_sim = np.mean([r['sbert_sim_mean'] for r in results])
    avg_two_tower_rating = np.mean([r['two_tower_rating_mean'] for r in results])
    avg_sbert_rating = np.mean([r['sbert_rating_mean'] for r in results])
    avg_overlap = np.mean([r['overlap_ratio'] for r in results])
    avg_two_tower_skills = np.mean([r['two_tower_skill_diversity'] for r in results])
    avg_sbert_skills = np.mean([r['sbert_skill_diversity'] for r in results])
    
    print("\nAverage Metrics Across All Queries:")
    print(f"Average Two-Tower similarity score: {avg_two_tower_sim:.4f}")
    print(f"Average SBERT similarity score: {avg_sbert_sim:.4f}")
    print(f"Average Two-Tower rating: {avg_two_tower_rating:.2f}")
    print(f"Average SBERT rating: {avg_sbert_rating:.2f}")
    print(f"Average recommendation overlap: {avg_overlap:.2%}")
    print(f"Average Two-Tower skill diversity: {avg_two_tower_skills:.2f}")
    print(f"Average SBERT skill diversity: {avg_sbert_skills:.2f}")

if __name__ == "__main__":
    main() 