import tensorflow as tf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import precision_score, recall_score, ndcg_score
from typing import List, Dict, Tuple, Optional
import os
import sys
import pickle
from datetime import datetime
import importlib.util

# Add parent directory for package import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

import config
import utils

# Import TwoTowerRecommender from file with parentheses
spec = importlib.util.spec_from_file_location("two_tower_cf", "two_recomendation(CF).py")
two_tower_cf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(two_tower_cf)
TwoTowerRecommender = two_tower_cf.TwoTowerRecommender
filter_positive_interactions = two_tower_cf.filter_positive_interactions

class TwoTowerEvaluator:
    """Evaluates the Two-Tower recommender system using various metrics."""
    
    def __init__(self, courses_df: pd.DataFrame, interactions_df: pd.DataFrame):
        """
        Initialize the evaluator.
        
        Args:
            courses_df: DataFrame containing course information
            interactions_df: DataFrame containing user interactions
        """
        self.courses_df = courses_df
        self.interactions_df = interactions_df
        self.positive_interactions = filter_positive_interactions(interactions_df)
        self.recommender = None
        self.evaluation_results = {}
        
    def load_trained_model(self, model_weights_path: str) -> bool:
        """
        Load a trained Two-Tower model.
        
        Args:
            model_weights_path: Path to the saved model weights
            
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            self.recommender = TwoTowerRecommender(
                courses_df=self.courses_df,
                user_interactions_df=self.positive_interactions,
                model_weights_path=model_weights_path
            )
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
            
    def evaluate_recommendations(self, test_users: List[str], k_values: List[int] = [5, 10, 20]) -> Dict:
        """
        Evaluate recommendation quality for a set of test users.
        
        Args:
            test_users: List of user IDs to evaluate
            k_values: List of k values for top-k evaluation
            
        Returns:
            Dictionary containing evaluation metrics
        """
        if self.recommender is None:
            raise ValueError("Model not loaded. Call load_trained_model first.")
            
        results = {}
        
        for k in k_values:
            precision_scores = []
            recall_scores = []
            ndcg_scores = []
            
            for user_id in test_users:
                # Get ground truth items for user
                user_items = set(self.positive_interactions[
                    self.positive_interactions['user_id'] == user_id
                ]['item_id'])
                
                if not user_items:
                    continue
                    
                # Get recommendations
                recommendations = self.recommender.get_recommendations(user_id, top_k=k)
                if recommendations.empty:
                    continue
                
                # Debug print to check column names
                print(f"Available columns in recommendations: {recommendations.columns.tolist()}")
                    
                # Use the correct column name for item IDs
                item_id_column = 'item_id' if 'item_id' in recommendations.columns else 'course_id'
                recommended_items = set(recommendations[item_id_column])
                
                # Calculate metrics
                hits = len(user_items.intersection(recommended_items))
                precision = hits / k
                recall = hits / len(user_items) if user_items else 0
                
                # NDCG calculation
                relevance_scores = [1 if item in user_items else 0 for item in recommendations[item_id_column]]
                ndcg = ndcg_score([relevance_scores], [relevance_scores], k=k)
                
                precision_scores.append(precision)
                recall_scores.append(recall)
                ndcg_scores.append(ndcg)
            
            # Aggregate metrics
            results[f'precision@{k}'] = np.mean(precision_scores) if precision_scores else 0
            results[f'recall@{k}'] = np.mean(recall_scores) if recall_scores else 0
            results[f'ndcg@{k}'] = np.mean(ndcg_scores) if ndcg_scores else 0
            
        return results
        
    def evaluate_content_recommendations(self, test_queries: List[str], k_values: List[int] = [5, 10, 20]) -> Dict:
        """
        Evaluate content-based recommendations using SBERT.
        
        Args:
            test_queries: List of test queries
            k_values: List of k values for top-k evaluation
            
        Returns:
            Dictionary containing evaluation metrics
        """
        if self.recommender is None:
            raise ValueError("Model not loaded. Call load_trained_model first.")
            
        results = {}
        
        for k in k_values:
            similarity_scores = []
            
            for query in test_queries:
                recommendations = self.recommender.get_sbert_recommendations(query, top_k=k)
                if not recommendations.empty:
                    similarity_scores.extend(recommendations['similarity_score'].tolist())
            
            results[f'mean_similarity@{k}'] = np.mean(similarity_scores) if similarity_scores else 0
            results[f'max_similarity@{k}'] = np.max(similarity_scores) if similarity_scores else 0
            
        return results
        
    def evaluate_model_performance(self, test_size: float = 0.2) -> Dict:
        """
        Evaluate model training and inference performance.
        
        Args:
            test_size: Proportion of data to use for testing
            
        Returns:
            Dictionary containing performance metrics
        """
        if self.recommender is None:
            raise ValueError("Model not loaded. Call load_trained_model first.")
            
        # Prepare data
        train_dataset, test_dataset = self.recommender.prepare_data_for_training()
        
        # Compile model before training
        self.recommender.compile_model()
        
        # Measure training time
        start_time = datetime.now()
        history = self.recommender.train_model(train_dataset, test_dataset)
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Measure inference time
        inference_times = []
        for _ in range(10):  # Run 10 times for average
            start_time = datetime.now()
            _ = self.recommender.get_recommendations(
                self.positive_interactions['user_id'].iloc[0],
                top_k=10
            )
            inference_times.append((datetime.now() - start_time).total_seconds())
            
        return {
            'training_time': training_time,
            'avg_inference_time': np.mean(inference_times),
            'std_inference_time': np.std(inference_times),
            'final_loss': history.history['loss'][-1] if history else None,
            'final_val_loss': history.history['val_loss'][-1] if history else None
        }
        
    def generate_evaluation_report(self, output_dir: str = 'evaluation_results') -> None:
        """
        Generate comprehensive evaluation report.
        
        Args:
            output_dir: Directory to save evaluation results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Select test users (users with sufficient interactions)
        user_interaction_counts = self.positive_interactions['user_id'].value_counts()
        test_users = user_interaction_counts[user_interaction_counts >= 5].index.tolist()[:100]
        
        # Select test queries
        test_queries = [
            "machine learning algorithms",
            "data science fundamentals",
            "python programming",
            "web development",
            "artificial intelligence"
        ]
        
        # Run evaluations
        print("Evaluating collaborative recommendations...")
        collab_results = self.evaluate_recommendations(test_users)
        
        print("Evaluating content-based recommendations...")
        content_results = self.evaluate_content_recommendations(test_queries)
        
        print("Evaluating model performance...")
        performance_results = self.evaluate_model_performance()
        
        # Combine results
        self.evaluation_results = {
            'collaborative': collab_results,
            'content_based': content_results,
            'performance': performance_results
        }
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save as CSV
        results_df = pd.DataFrame({
            'metric': list(collab_results.keys()) + list(content_results.keys()),
            'value': list(collab_results.values()) + list(content_results.values())
        })
        results_df.to_csv(
            os.path.join(output_dir, f'evaluation_results_{timestamp}.csv'),
            index=False
        )
        
        # Generate plots
        self._generate_evaluation_plots(output_dir, timestamp)
        
        # Save performance metrics
        with open(os.path.join(output_dir, f'performance_metrics_{timestamp}.txt'), 'w') as f:
            f.write("Model Performance Metrics:\n")
            f.write(f"Training Time: {performance_results['training_time']:.2f} seconds\n")
            f.write(f"Average Inference Time: {performance_results['avg_inference_time']:.4f} seconds\n")
            f.write(f"Final Training Loss: {performance_results['final_loss']:.4f}\n")
            f.write(f"Final Validation Loss: {performance_results['final_val_loss']:.4f}\n")
            
    def _generate_evaluation_plots(self, output_dir: str, timestamp: str) -> None:
        """
        Generate evaluation plots.
        
        Args:
            output_dir: Directory to save plots
            timestamp: Timestamp for file naming
        """
        # Set style
        plt.style.use('default')  # Use default style instead of seaborn
        
        # Plot collaborative metrics
        collab_metrics = self.evaluation_results['collaborative']
        k_values = [int(k.split('@')[1]) for k in collab_metrics.keys() if k.startswith('precision')]
        
        plt.figure(figsize=(12, 6))
        for metric in ['precision', 'recall', 'ndcg']:
            values = [collab_metrics[f'{metric}@{k}'] for k in k_values]
            plt.plot(k_values, values, marker='o', label=metric.upper())
            
        plt.xlabel('k')
        plt.ylabel('Score')
        plt.title('Collaborative Filtering Metrics')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, f'collab_metrics_{timestamp}.png'))
        plt.close()
        
        # Plot content-based metrics
        content_metrics = self.evaluation_results['content_based']
        k_values = [int(k.split('@')[1]) for k in content_metrics.keys() if k.startswith('mean_similarity')]
        
        plt.figure(figsize=(12, 6))
        for metric in ['mean_similarity', 'max_similarity']:
            values = [content_metrics[f'{metric}@{k}'] for k in k_values]
            plt.plot(k_values, values, marker='o', label=metric.replace('_', ' ').title())
            
        plt.xlabel('k')
        plt.ylabel('Similarity Score')
        plt.title('Content-Based Recommendation Metrics')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, f'content_metrics_{timestamp}.png'))
        plt.close()

def main():
    """Main execution function."""
    try:
        # Load data
        print("Loading course data...")
        courses_df = utils.load_course_data(config.COURSE_DATA_PATH)
        if courses_df is None or courses_df.empty:
            raise ValueError("Failed to load course data or data is empty")
            
        print("Loading interaction data...")
        interactions_df = pd.read_csv(config.INTERACTION_DATA_PATH, encoding='utf-8')
        if interactions_df.empty:
            raise ValueError("Interaction data is empty")
            
        # Initialize evaluator
        print("Initializing evaluator...")
        evaluator = TwoTowerEvaluator(courses_df, interactions_df)
        
        # Load trained model
        print("Loading trained model...")
        if not evaluator.load_trained_model(config.TWO_TOWER_MODEL_WEIGHTS_PATH):
            raise ValueError("Failed to load trained model")
            
        # Generate evaluation report
        print("Generating evaluation report...")
        evaluator.generate_evaluation_report()
        
        print("Evaluation complete! Check the 'evaluation_results' directory for detailed reports.")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 