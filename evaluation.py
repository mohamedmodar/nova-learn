import pandas as pd
import numpy as np
import tensorflow as tf
from adapted_two_tower_model import CourseRecommender, MAX_HISTORY_LENGTH
from tqdm import tqdm

# --- Configuration ---
MODEL_PATH = 'two_tower_real_interactions.weights.h5'
INTERACTIONS_PATH = 'data/fake_interactions.csv'
TOP_K = 10 # Number of recommendations to generate for evaluation

def evaluate_model():
    """
    Performs an offline evaluation of the Two-Tower model using hold-out validation.
    For each user, it uses their interaction history (except the last item) to predict
    the last item.
    """
    print("--- Starting Model Evaluation ---")
    
    # 1. Load the recommender system
    try:
        recommender = CourseRecommender(model_path=MODEL_PATH)
        if recommender.model is None or recommender.item_embeddings_norm is None:
            print("❌ Recommender or item embeddings failed to load. Aborting.")
            return
    except Exception as e:
        print(f"❌ Error loading the recommender: {e}")
        return
        
    print(f"✅ Recommender loaded with model weights from '{MODEL_PATH}'.")

    # 2. Load and process interaction data
    try:
        interactions_df = pd.read_csv(INTERACTIONS_PATH)
        # Ensure interactions are sorted by time to correctly identify the last item
        if 'timestamp' in interactions_df.columns:
            interactions_df = interactions_df.sort_values(by='timestamp')
        print(f"✅ Loaded {len(interactions_df)} interactions from '{INTERACTIONS_PATH}'.")
    except FileNotFoundError:
        print(f"❌ Interaction data not found at '{INTERACTIONS_PATH}'. Aborting.")
        return

    # --- FIX: Apply the same data cleaning and mapping as in the training script ---
    courses_df = pd.read_csv('data/final(final).csv')
    item_id_to_index_map = {item_id: i for i, item_id in enumerate(courses_df['item_id'])}
    
    interactions_df['item_index'] = interactions_df['item_id'].map(item_id_to_index_map)
    interactions_df.dropna(subset=['item_index'], inplace=True)
    interactions_df['item_id'] = interactions_df['item_index'].astype('int64')
    print(f"Cleaned and mapped interactions: {len(interactions_df)} rows remain.")

    # Group interactions by user to form histories
    user_histories = interactions_df.groupby('user_id')['item_id'].apply(list)
    
    # Filter for users with enough history for a meaningful test
    testable_users = user_histories[user_histories.apply(len) > 1]
    print(f"Found {len(testable_users)} users with sufficient history for evaluation.")

    if len(testable_users) == 0:
        print("❌ No users with enough history to evaluate. Need at least 2 interactions per user.")
        return

    # 3. Perform evaluation
    hits = 0
    total_reciprocal_rank = 0.0

    print(f"\nEvaluating model performance on {len(testable_users)} users...")
    
    # Use tqdm for a progress bar
    for user_id, history in tqdm(testable_users.items(), desc="Evaluating Users"):
        # The user's history for prediction is all but their last interaction
        history_for_prediction = history[:-1]
        # The ground truth is the last item the user interacted with
        ground_truth_item_id = history[-1]
        
        if not history_for_prediction:
            continue

        # Get top K recommendations from the model
        try:
            recommendations = recommender.recommend(user_interaction_history=history_for_prediction, top_k=TOP_K)
            
            if recommendations.empty:
                continue

            recommended_ids = recommendations.index.tolist()

            # Check for a "hit"
            if ground_truth_item_id in recommended_ids:
                hits += 1
                # Calculate reciprocal rank
                rank = recommended_ids.index(ground_truth_item_id) + 1
                total_reciprocal_rank += 1.0 / rank

        except Exception as e:
            print(f"\nError recommending for user {user_id}: {e}")
            continue
            
    # 4. Calculate and print final metrics
    num_evaluated_users = len(testable_users)
    hit_rate_at_k = (hits / num_evaluated_users) * 100 if num_evaluated_users > 0 else 0
    mrr_at_k = total_reciprocal_rank / num_evaluated_users if num_evaluated_users > 0 else 0

    print("\n--- 📈 Evaluation Results ---")
    print(f"Total Users Evaluated: {num_evaluated_users}")
    print(f"Top K Recommendations:   {TOP_K}")
    print("-" * 30)
    print(f"✅ Hit Rate @ {TOP_K}:     {hit_rate_at_k:.2f}%")
    print(f"✅ MRR @ {TOP_K}:        {mrr_at_k:.4f}")
    print("-" * 30)
    print("\nHit Rate: The percentage of users for whom the correct next item was in the top K recommendations.")
    print("MRR: The average of the reciprocal ranks of the correct item. Higher is better (1.0 is perfect).")

if __name__ == "__main__":
    evaluate_model() 