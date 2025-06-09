import tensorflow as tf
import tensorflow_recommenders as tfrs # Import tfrs
import numpy as np
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import os # Import os for path handling
import sys # Import sys for path manipulation
import matplotlib.pyplot as plt
import seaborn as sns
# from faker import Faker # Faker not needed for reading existing file
import random # For random choices

# --- Add Parent Directory for Package Import ---
# This ensures that 'config' and 'utils' can be imported if this script is in a subdirectory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# Now import from the package
import config # Assuming config.py is in the parent directory
import utils # Assuming utils.py is in the parent directory

# Constants (these are now primarily set in config.py)
SBERT_EMBEDDING_DIM = 384  # Dimension of our SBERT embeddings (for all-MiniLM-L6-v2)


# --- Model Architectures ---
class UserModel(tf.keras.Model):
    """Defines the user tower of the Two-Tower model."""
    def __init__(self, user_vocab, embedding_dim):
        super().__init__()
        self.user_embedding = tf.keras.Sequential([
            tf.keras.layers.StringLookup(
                vocabulary=user_vocab, mask_token=None
            ),
            tf.keras.layers.Embedding(len(user_vocab) + 1, embedding_dim),
            tf.keras.layers.Dense(embedding_dim, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(embedding_dim, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(embedding_dim)
        ])

    def call(self, user_id):
        """Forward pass for the user tower."""
        return tf.nn.l2_normalize(self.user_embedding(user_id), axis=1)

class ItemModel(tf.keras.Model):
    """Defines the item (course) tower of the Two-Tower model."""
    def __init__(self, item_vocab, embedding_dim, item_content_embeddings=None):
        """
        Initializes the item tower.

        Args:
            item_vocab (list): List of unique item IDs.
            embedding_dim (int): Dimension for the learned item ID embeddings.
            item_content_embeddings (np.ndarray, optional): Pre-computed SBERT embeddings 
                                                            for item content. Shape should be 
                                                            (num_items, sbert_embedding_dim).
                                                            Indices must align with item_vocab.
        """
        super().__init__()
        self.item_vocab_size = len(item_vocab) + 1 # +1 for unknown token
        self.item_id_embedding_dim = embedding_dim
        self.item_content_embeddings = item_content_embeddings
        self.content_embedding_dim = item_content_embeddings.shape[1] if item_content_embeddings is not None else 0
        
        print(f"Item Tower Init: Vocab size={self.item_vocab_size}, ID Emb Dim={self.item_id_embedding_dim}, Content Emb Dim={self.content_embedding_dim}")

        # Layer to lookup item ID
        self.string_lookup = tf.keras.layers.StringLookup(
            vocabulary=item_vocab, mask_token=None
        )

        # Embedding layer for item IDs (learned)
        self.item_id_embedding = tf.keras.layers.Embedding(
            self.item_vocab_size, 
            self.item_id_embedding_dim
        )

        # If content embeddings are provided, prepare to use them
        if self.item_content_embeddings is not None:
            self.item_content_embeddings = self.item_content_embeddings.astype(np.float32)
            zero_embedding = np.zeros((1, self.content_embedding_dim), dtype=np.float32)
            content_embeddings_with_oov = np.vstack([zero_embedding, self.item_content_embeddings])
            
            self.content_embedding_layer = tf.keras.layers.Embedding(
                input_dim=self.item_vocab_size,
                output_dim=self.content_embedding_dim,
                embeddings_initializer=tf.keras.initializers.Constant(content_embeddings_with_oov),
                trainable=False
            )
            print("Item Tower: Using pre-trained content embeddings.")
            
            # Dense layers for content embeddings
            self.content_dense = tf.keras.Sequential([
                tf.keras.layers.Dense(embedding_dim, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(embedding_dim, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(embedding_dim)
            ])
        else:
            print("Item Tower: Using only learned ID embeddings.")
            
        # Final projection layer
        # This layer ensures the output dimension matches the shared embedding dimension
        self.final_projection = tf.keras.Sequential([
            tf.keras.layers.Dense(config.TWO_TOWER_SHARED_EMBEDDING_DIM, activation='relu'), # Project to shared dim
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(config.TWO_TOWER_SHARED_EMBEDDING_DIM) # Final output is shared dim
        ])

    def call(self, item_id):
        """Forward pass for the item tower."""
        item_index = self.string_lookup(item_id)
        id_embedding = self.item_id_embedding(item_index)

        if self.item_content_embeddings is not None:
            content_embedding = self.content_embedding_layer(item_index)
            content_projected = self.content_dense(content_embedding)
            combined_embedding = tf.concat([id_embedding, content_projected], axis=1)
        else:
            combined_embedding = id_embedding
            
        final_embedding = self.final_projection(combined_embedding)
        return tf.nn.l2_normalize(final_embedding, axis=1)

class TwoTowerModel(tfrs.Model): # Corrected to tfrs.Model
    """The main Two-Tower model integrating user and item towers."""
    def __init__(self, user_model, item_model, item_ids_vocab, item_dataset, item_titles_map):
        super().__init__()
        self.user_model = user_model
        self.item_model = item_model
        self.item_ids_vocab = tf.constant(item_ids_vocab)
        self.item_titles_map = item_titles_map
        self.item_dataset = item_dataset # Store the dataset of item IDs

        # Prepare candidates dataset: map item IDs to embeddings
        # FactorizedTopK expects a dataset of candidate embeddings.
        candidate_embeddings_dataset = self.item_dataset.batch(128).map(self.item_model)

        try:
            # FIX: Supply the candidate_embeddings_dataset to FactorizedTopK at initialization
            self.retrieval_metrics = tfrs.metrics.FactorizedTopK(
                candidates=candidate_embeddings_dataset
            )
            print("TwoTowerModel: Initialized FactorizedTopK metric with candidate embeddings dataset.")
            self.task = tfrs.tasks.Retrieval(
                metrics=self.retrieval_metrics
            )
            print("TwoTowerModel: Initialized tfrs.tasks.Retrieval.")
        except Exception as e: # Catch potential errors during init
            print(f"ERROR during FactorizedTopK/Retrieval initialization: {e}")
            import traceback
            traceback.print_exc()
            raise e # Re-raise to stop execution

    def compute_loss(self, features, training=False):
        """Computes the loss for a batch of features."""
        user_embeddings = self.user_model(features["user_id"])
        item_embeddings = self.item_model(features["item_id"])

        # Retrieval task handles metric computation using the candidates provided at init
        return self.task(
            user_embeddings, 
            item_embeddings, 
            compute_metrics=not training
        )
    

class TwoTowerRecommender:
    """
    Handles the setup, training, and prediction for the Two-Tower model.
    Uses the user-specified columns: Skills, title, adjusted_rating, descrition.
    """
    def __init__(self, courses_df, user_interactions_df, model_weights_path=None):
        """
        Initialize the Two-Tower Recommender.

        Args:
            courses_df (pd.DataFrame): DataFrame containing course information
            user_interactions_df (pd.DataFrame): DataFrame containing user-item interactions
            model_weights_path (str, optional): Path to saved model weights
        """
        self.courses_df = courses_df
        self.user_interactions_df = user_interactions_df
        self.model_weights_path = model_weights_path
        
        # Initialize embeddings
        self.course_embeddings = None
        self.item_embeddings_precomputed = None
        self.item_embeddings_norm = None
        
        # Load SBERT embeddings for course content
        self._load_item_content_embeddings()
        
        # Prepare vocabularies
        self._prepare_vocabularies()
        
        # Build the model
        self.model = self._build_model()
        
        # Load weights if provided
        if self.model is not None and model_weights_path and os.path.exists(model_weights_path):
            self.load_model_weights()

        # Load SBERT model for get_sbert_recommendations
        self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("SBERT model 'all-MiniLM-L6-v2' loaded for content-based recommendations.")


    def _load_item_content_embeddings(self):
        """Load pre-computed SBERT embeddings for course content."""
        try:
            # Using absolute path from config
            if os.path.exists(config.SBERT_EMBEDDINGS_PATH):
                with open(config.SBERT_EMBEDDINGS_PATH, 'rb') as f:
                    self.course_embeddings = pickle.load(f)
                print(f"Loaded course SBERT embeddings from {config.SBERT_EMBEDDINGS_PATH}")
            else:
                print(f"Warning: Course SBERT embeddings file not found at {config.SBERT_EMBEDDINGS_PATH}")
                self.course_embeddings = None
        except Exception as e:
            print(f"Error loading course SBERT embeddings: {e}")
            self.course_embeddings = None

    def _prepare_vocabularies(self):
        """Creates unique vocabularies for users and items."""
        print("Preparing vocabularies and maps...")
        # --- DEBUG: Print item_id dtype from courses_df before creating item_vocab ---
        print(f"DEBUG: courses_df['item_id'] dtype: {self.courses_df['item_id'].dtype}")
        print(f"DEBUG: Sample courses_df['item_id'] values: {self.courses_df['item_id'].head().tolist()}")


        self.user_vocab = self.user_interactions_df["user_id"].unique().tolist()
        # Item vocabulary should be derived from the courses_df in the order it was loaded
        # so that it aligns with the item_content_embeddings (if used).
        self.item_vocab = self.courses_df["item_id"].tolist() 
        print(f"Item vocabulary size (unique IDs): {len(set(self.item_vocab))}") # Should match len(courses_df)
        print(f"User vocabulary size: {len(self.user_vocab)}")
        # Create item title map (changed name for consistency)
        self.item_titles_map = pd.Series(self.courses_df["title"].values, index=self.courses_df["item_id"]).to_dict()

    def _build_model(self):
        """Builds the Keras TwoTowerModel structure."""
        print("Building Two-Tower Keras model...")
        if not self.user_vocab or not self.item_vocab:
            print("Error: Vocabularies not prepared. Cannot build model.")
            return None
            
        # Use shared embedding dimension from config for user tower output
        user_model = UserModel(self.user_vocab, config.TWO_TOWER_SHARED_EMBEDDING_DIM)
        
        # item_id_embedding_dim in ItemModel refers to the embedding dimension of the learned item ID.
        # This parameter is distinct from SBERT_EMBEDDING_DIM.
        item_id_embedding_dim_for_model = config.TWO_TOWER_ITEM_EMBEDDING_DIM # Use from config

        # Check if we have SBERT embeddings and they match our course data
        if self.course_embeddings is not None:
            if len(self.course_embeddings) != len(self.item_vocab):
                print(f"Warning: Number of SBERT embeddings ({len(self.course_embeddings)}) does not match number of courses ({len(self.item_vocab)}). Using only learned embeddings.")
                self.course_embeddings = None
            else:
                print(f"Using SBERT embeddings with shape: {self.course_embeddings.shape}")
        else:
            print("No SBERT embeddings available. Using only learned embeddings.")

        item_model = ItemModel(
            item_vocab=self.item_vocab,
            embedding_dim=item_id_embedding_dim_for_model,
            item_content_embeddings=self.course_embeddings
        )
            
        # Prepare item data tensor for the retrieval task candidates
        item_dataset_for_candidates = tf.data.Dataset.from_tensor_slices(
            tf.constant(self.item_vocab)
        )

        try:
            self.model = TwoTowerModel(
                user_model=user_model,
                item_model=item_model,
                item_ids_vocab=self.item_vocab,
                item_dataset=item_dataset_for_candidates,
                item_titles_map=self.item_titles_map
            )
            print("Two-Tower Keras model built successfully.")
            return self.model
        except Exception as e:
            print(f"Error building Two-Tower model: {e}")
            import traceback
            traceback.print_exc()
            return None

    def prepare_data_for_training(self):
        """Converts interaction data into TensorFlow Datasets for training."""
        if self.user_interactions_df is None or self.user_interactions_df.empty:
            print("Error: No interaction data available for training.")
            return None, None
            
        # Select relevant columns for training (user_id, item_id)
        # TFRS Retrieval task expects features to be a dictionary where keys are feature names
        # and values are tensors.
        interactions_dict = {
            "user_id": np.array(self.user_interactions_df["user_id"]),
            "item_id": np.array(self.user_interactions_df["item_id"]),
            # If you had a timestamp feature that TFRS could use for negative sampling, add it here.
            # "timestamp": np.array(self.user_interactions_df["timestamp"])
        }
        dataset = tf.data.Dataset.from_tensor_slices(interactions_dict)

        # Shuffle and split data
        tf.random.set_seed(42)
        shuffled = dataset.shuffle(len(self.user_interactions_df), seed=42, reshuffle_each_iteration=False)

        train_size = int(len(self.user_interactions_df) * (1 - config.TWO_TOWER_TEST_SPLIT))
        train_dataset = shuffled.take(train_size)
        test_dataset = shuffled.skip(train_size)

        # Batch and cache datasets
        train_dataset = train_dataset.batch(config.TWO_TOWER_BATCH_SIZE).cache()
        test_dataset = test_dataset.batch(config.TWO_TOWER_BATCH_SIZE).cache()
            
        print(f"Training dataset size: {train_size} interactions.")
        print(f"Test dataset size: {len(self.user_interactions_df) - train_size} interactions.")
        return train_dataset, test_dataset

    def compile_model(self):
        """Compiles the Keras model with optimizer."""
        if self.model is None:
            print("Error: Model not built. Cannot compile.")
            return
        self.model.compile(optimizer=tf.keras.optimizers.Adagrad(learning_rate=config.TWO_TOWER_LEARNING_RATE))
        print("Model compiled.")

    def _precompute_item_embeddings(self):
        """Pre-computes item embeddings using the trained model."""
        if self.model is None:
            print("Error: Model not available. Cannot pre-compute embeddings.")
            return False
            
        try:
            # Create a tensor of all item_ids
            all_item_ids_tensor = tf.constant(self.item_vocab)
            
            # Get embeddings from the item model
            self.item_embeddings_precomputed = self.model.item_model(all_item_ids_tensor)
            
            # Normalize embeddings
            self.item_embeddings_norm = tf.nn.l2_normalize(self.item_embeddings_precomputed, axis=1)
            
            print("Successfully pre-computed item embeddings.")
            return True
        except Exception as e:
            print(f"Error pre-computing item embeddings: {e}")
            import traceback
            traceback.print_exc()
            return False

    def train_model(self, train_dataset, test_dataset):
        """Trains the compiled Keras model."""
        if self.model is None or not self.model._is_compiled:
            print("Error: Model not compiled. Cannot train.")
            return None
        if train_dataset is None or test_dataset is None:
            print("Error: Training or test dataset not available. Cannot train.")
            return None
                
        print(f"Training model for {config.TWO_TOWER_EPOCHS} epochs...")
        history = self.model.fit(
            train_dataset,
            validation_data=test_dataset,
            epochs=config.TWO_TOWER_EPOCHS,
            verbose=1
        )
        
        # Pre-compute item embeddings after training
        if not self._precompute_item_embeddings():
            print("Warning: Failed to pre-compute item embeddings after training.")
            
        return history

    def save_model_weights(self):
        """Saves the trained model weights."""
        if self.model is None:
            print("Error: No model to save.")
            return
        try:
            # Using absolute path from config
            os.makedirs(os.path.dirname(config.TWO_TOWER_MODEL_WEIGHTS_PATH), exist_ok=True)
            self.model.save_weights(config.TWO_TOWER_MODEL_WEIGHTS_PATH)
            print(f"Model weights saved successfully to {config.TWO_TOWER_MODEL_WEIGHTS_PATH}")
        except Exception as e:
            print(f"Error saving model weights: {e}")

    def load_model_weights(self):
        """Loads pre-trained model weights."""
        if self.model is None:
            print("Model structure not built. Attempting to build...")
            self._build_model()
            if self.model is None:
                print("Failed to build model structure. Cannot load weights.")
                return False
            print("Model structure built.")

        # Using absolute path from config
        if not os.path.exists(config.TWO_TOWER_MODEL_WEIGHTS_PATH):
            print(f"Error: Model weights file not found at {config.TWO_TOWER_MODEL_WEIGHTS_PATH}")
            return False
        try:
            # Need to run a dummy forward pass to build layers before loading weights
            # Create dummy input based on expected feature names
            dummy_user_id_val = self.user_vocab[0] if self.user_vocab else "dummy_user_0"
            dummy_item_id_val = self.item_vocab[0] if self.item_vocab else "dummy_item_0"
            dummy_input = {
                "user_id": tf.constant([dummy_user_id_val]),
                "item_id": tf.constant([dummy_item_id_val])
            }
            # We need to compute loss once to ensure metrics are built
            _ = self.model.compute_loss(dummy_input, training=False)
            print("Ran dummy compute_loss pass to build layers and metrics.")
                
            self.model.load_weights(config.TWO_TOWER_MODEL_WEIGHTS_PATH)
            print(f"Model weights loaded successfully from {config.TWO_TOWER_MODEL_WEIGHTS_PATH}")
            
            # Pre-compute item embeddings after loading weights
            if not self._precompute_item_embeddings():
                print("Warning: Failed to pre-compute item embeddings after loading weights.")
                return False
                
            return True
        except Exception as e:
            print(f"Error loading model weights: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_recommendations(self, user_id, top_k=10):
        """Generates top_k recommendations for a given user_id using the trained Two-Tower model."""
        if self.model is None or self.item_embeddings_precomputed is None:
            print("Model not available or item embeddings not pre-computed. Attempting to load weights and re-compute...")
            # If load_model_weights is successful, it also pre-computes item_embeddings_norm
            if not self.load_model_weights():
                print("Failed to load model weights. Cannot generate recommendations.")
                return pd.DataFrame()
            print("Model weights loaded and item embeddings pre-computed.")
                
        if user_id not in self.user_vocab:
            print(f"Warning: User ID '{user_id}' not found in training data vocabulary. Cannot generate personalized recommendations.")
            # Fallback: maybe return popular items or content-based items if user is new.
            # For now, return empty DataFrame.
            return pd.DataFrame() 

        # Retrieve user embedding
        user_embedding = self.model.user_model(tf.constant([user_id]))
        # user_model.call already normalizes output, no need for explicit normalization here.
        
        # Compute dot product similarity with all pre-computed item embeddings
        # self.item_embeddings_norm contains the normalized final item embeddings
        # Result shape: (1, num_items)
        similarity_scores = tf.matmul(user_embedding, self.item_embeddings_norm, transpose_b=True) # user_embedding is already normalized
        similarity_scores = tf.squeeze(similarity_scores, axis=0) # Shape: (num_items,)
        
        # Get top-k indices and scores
        top_scores, top_indices = tf.math.top_k(similarity_scores, k=min(top_k, len(self.item_vocab)))
        
        # Map indices back to item IDs and then to titles
        recommended_item_ids = [self.item_vocab[idx] for idx in top_indices.numpy()]
        recommended_scores = top_scores.numpy()

        # Create DataFrame for recommendations
        recommendations_df = pd.DataFrame({
            'item_id': recommended_item_ids,
            'title': [self.item_titles_map.get(item_id, "Unknown Title") for item_id in recommended_item_ids],
            'similarity_score': recommended_scores
        })
        
        # --- DEBUG: Print item_id values and types right before merge ---
        print("\nDEBUG: Two-Tower recommendations_df before merge:")
        print(f"  item_id dtype: {recommendations_df['item_id'].dtype}")
        print(f"  Sample item_id values: {recommendations_df['item_id'].head().tolist()}")
        print(f"DEBUG: courses_df_loaded (self.courses_df) before merge:")
        print(f"  item_id dtype: {self.courses_df['item_id'].dtype}")
        print(f"  Sample item_id values: {self.courses_df['item_id'].head().tolist()}")
        print("-" * 50)


        # Merge with courses_df to get full course details
        final_recommendations = recommendations_df.merge(self.courses_df, on='item_id', how='left')
        
        # Select and reorder desired columns for output
        # Ensuring 'descrition' is correctly spelled and included
        output_cols = ['title', 'similarity_score', 'adjusted_rating', 'level', 'descrition', 'url', 'skills_list']
        # Filter for existing columns to avoid KeyErrors
        existing_output_cols = [col for col in output_cols if col in final_recommendations.columns]

        return final_recommendations[existing_output_cols]

    def get_sbert_recommendations(self, query_text, top_k=5):
        """
        Generates content-based recommendations using raw SBERT similarity for a given text query.
        """
        if self.sbert_model is None:
            print("Error: SBERT model not loaded. Cannot generate content-based recommendations.")
            return pd.DataFrame()
        if self.course_embeddings is None:
            print("Error: Course SBERT embeddings not available. Cannot generate content-based recommendations.")
            return pd.DataFrame()
        if self.courses_df.empty:
            print("Error: Course DataFrame is empty. Cannot generate content-based recommendations.")
            return pd.DataFrame()

        try:
            # Encode the query text
            query_embedding = self.sbert_model.encode(query_text, convert_to_tensor=True)
            
            # Compute cosine similarity between query embedding and all course embeddings
            cosine_scores = util.cos_sim(query_embedding, torch.tensor(self.course_embeddings))
            
            # Flatten the scores tensor and convert to numpy for sorting
            cosine_scores_np = cosine_scores.cpu().numpy().flatten()
            
            # Get top-k indices based on similarity scores
            top_indices = np.argsort(cosine_scores_np)[::-1][:top_k]
            top_scores = cosine_scores_np[top_indices]
            
            # Map indices back to item_ids using the item_vocab
            recommended_item_ids = [self.item_vocab[idx] for idx in top_indices]
            
            # Create a DataFrame for recommendations
            recommendations_df = pd.DataFrame({
                'item_id': recommended_item_ids,
                'sbert_similarity_score': top_scores
            })
            
            # --- DEBUG: Print item_id values and types right before merge (SBERT) ---
            print("\nDEBUG: SBERT recommendations_df before merge:")
            print(f"  item_id dtype: {recommendations_df['item_id'].dtype}")
            print(f"  Sample item_id values: {recommendations_df['item_id'].head().tolist()}")
            print(f"DEBUG: courses_df_loaded (self.courses_df) before merge (SBERT):")
            print(f"  item_id dtype: {self.courses_df['item_id'].dtype}")
            print(f"  Sample item_id values: {self.courses_df['item_id'].head().tolist()}")
            print("-" * 50)


            # Merge with courses_df to get full course details
            final_recommendations = recommendations_df.merge(self.courses_df, on='item_id', how='left')
            
            # Select and reorder desired columns for output
            output_cols = ['title', 'sbert_similarity_score', 'adjusted_rating', 'level', 'descrition', 'url', 'skills_list']
            existing_output_cols = [col for col in output_cols if col in final_recommendations.columns]
            
            return final_recommendations[existing_output_cols]

        except Exception as e:
            print(f"Error generating SBERT recommendations: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()


# --- New function to filter positive interactions ---
def filter_positive_interactions(interactions_df, rating_threshold=3.5):
    """
    Filters the raw interactions DataFrame to keep only positive interactions.
    
    Args:
        interactions_df (pd.DataFrame): The raw DataFrame of interactions.
        rating_threshold (float): Minimum rating value to be considered positive.
        
    Returns:
        pd.DataFrame: A DataFrame containing only 'user_id' and 'item_id' for positive interactions.
    """
    if interactions_df.empty:
        print("Warning: Input interactions_df is empty.")
        return pd.DataFrame(columns=['user_id', 'item_id'])

    # --- FIX: Change 'action_value' to 'value' as per your fake_interactions.csv structure ---
    interactions_df['value'] = pd.to_numeric(interactions_df['value'], errors='coerce') 
    
    # Consider 'click' and 'like' as positive
    positive_actions = interactions_df[interactions_df['interaction_type'].isin(['click', 'like'])] # 'interaction_type' is correct
    
    # Consider 'rating' above threshold as positive (and not NaN after conversion)
    positive_ratings = interactions_df[
        (interactions_df['interaction_type'] == 'rating') & # 'interaction_type' is correct
        (interactions_df['value'].notna()) & # Check for non-NaN in 'value' column
        (interactions_df['value'] >= rating_threshold) # Use 'value' for comparison
    ]
    
    # Concatenate all positive interactions
    positive_interactions = pd.concat([positive_actions, positive_ratings]).drop_duplicates(subset=['user_id', 'item_id'])
    
    # Return only user_id and item_id as required by TFRS Retrieval task
    print(f"Filtered to {len(positive_interactions)} positive interactions for training.")
    return positive_interactions[['user_id', 'item_id']]


# --- Main Execution Block ---
if __name__ == "__main__":
    print("Starting Two-Tower Recommender System execution...")

    # Load course data first (needed for recommender init)
    # Using absolute path from config
    courses_df_loaded = utils.load_course_data(config.COURSE_DATA_PATH)

    if courses_df_loaded is None or courses_df_loaded.empty:
        print("Error: Course data could not be loaded. Aborting. Ensure 'final(ready for model).csv' exists and utils.load_course_data works.")
    else:
        # --- Load user's existing fake_interactions.csv ---
        print(f"\n--- Loading user interactions from {config.INTERACTION_DATA_PATH} ---")
        try:
            raw_user_interactions_df = pd.read_csv(config.INTERACTION_DATA_PATH, encoding='latin1') # ADDED ENCODING HERE
            print(f"Loaded {len(raw_user_interactions_df)} raw user interactions from {config.INTERACTION_DATA_PATH}.")
        except FileNotFoundError:
            print(f"Error: {config.INTERACTION_DATA_PATH} not found. Please ensure 'fake_interactions.csv' is in the same directory as this script.")
            print("Aborting training. You might need to run 'generate_fake_interactions (1).py' to create this file first.")
            raw_user_interactions_df = pd.DataFrame() # Create empty DataFrame to gracefully exit

        if raw_user_interactions_df.empty:
            print("Error: User interactions DataFrame is empty or could not be loaded. Aborting.")
        else:
            # Filter raw interactions to get only positive interactions for training
            positive_user_interactions_df = filter_positive_interactions(
                raw_user_interactions_df,
                rating_threshold=3.5 # Define what constitutes a "positive" rating
            )

            if positive_user_interactions_df.empty:
                print("Error: No positive interactions found after filtering. Aborting training.")
            else:
                # --- Step 1: Initialize the Recommender with both DataFrames ---
                recommender = TwoTowerRecommender(
                    courses_df=courses_df_loaded,
                    user_interactions_df=positive_user_interactions_df, # Pass only positive interactions
                    model_weights_path=None # We will train it first
                ) 

                if recommender.course_embeddings is None:
                    print("Error: Course SBERT embeddings not loaded. Please ensure 'course_sbert_embeddings.pkl' exists in the 'models' directory and run generate_sbert_embeddings.py first.")
                elif recommender.model is None: # Check if model building failed
                    print("Error: TwoTowerModel could not be built during recommender initialization. Aborting training.")
                else:
                    # --- Step 2: Prepare data for training ---
                    print("\n--- Preparing Data for Training ---")
                    # prepare_data_for_training will take positive_user_interactions_df
                    train_ds, test_ds = recommender.prepare_data_for_training()

                    if train_ds is None or test_ds is None:
                        print("Error: Training or test datasets could not be prepared. Aborting training.")
                    else:
                        # --- Step 3: Train the Two-Tower Model ---
                        print("\n--- Training Two-Tower Model ---")
                        
                        # Compile the model
                        recommender.compile_model()

                        history = recommender.train_model(
                            train_ds, # Pass train dataset
                            test_ds # Pass test dataset (for validation)
                        )

                        if history:
                            print("\nTraining History:")
                            for key, value in history.history.items():
                                print(f"  {key}: {value[-1]:.4f}") # Print last value of each metric
                            
                            # Save the trained model weights
                            recommender.save_model_weights()
                        
                        # --- Step 4: Re-initialize Recommender to load trained weights and pre-compute item embeddings ---
                        print("\n--- Re-initializing Recommender with trained weights ---")
                        recommender_trained = TwoTowerRecommender(
                            courses_df=courses_df_loaded,
                            user_interactions_df=positive_user_interactions_df, # Pass positive interactions again (not strictly needed for inference but for consistency)
                            model_weights_path=config.TWO_TOWER_MODEL_WEIGHTS_PATH
                        )

                        # --- Step 5: Test Recommendations ---
                        print("\n--- Testing Recommendations ---")
                        if recommender_trained.courses_df is not None and recommender_trained.item_embeddings_norm is not None:
                            # Pick a random user from the provided fake data for testing
                            if not positive_user_interactions_df.empty:
                                sample_user_id = random.choice(positive_user_interactions_df['user_id'].tolist()) 
                            else:
                                sample_user_id = "user_0" # Fallback if no positive interactions
                                print(f"Warning: No positive interactions to sample from. Using default user_id: {sample_user_id}")

                            print(f"\nRecommendations for User: '{sample_user_id}' (using Two-Tower Model):")
                            recommendations_tt = recommender_trained.get_recommendations(user_id=sample_user_id, top_k=5)
                            if not recommendations_tt.empty:
                                # Improved printing for Two-Tower recommendations
                                for i, row in recommendations_tt.iterrows():
                                    print(f"  --- Recommendation {i+1} ---")
                                    print(f"  Title: {row.get('title', 'N/A')}")
                                    print(f"  Similarity Score: {row.get('similarity_score', 'N/A'):.4f}")
                                    print(f"  Adjusted Rating: {row.get('adjusted_rating', 'N/A'):.2f}")
                                    print(f"  Level: {row.get('level', 'N/A')}")
                                    # Ensure 'descrition' is used for description
                                    print(f"  Description: {row.get('descrition', 'N/A')}") 
                                    print(f"  URL: {row.get('url', 'N/A')}")
                                    # Ensure skills_list is handled as a list for proper display
                                    skills = row.get('skills_list', 'N/A')
                                    # Check if skills is a string representation of a list, and try to parse it
                                    if isinstance(skills, str) and skills.startswith('[') and skills.endswith(']'):
                                        try:
                                            import ast
                                            parsed_skills = ast.literal_eval(skills)
                                            if isinstance(parsed_skills, list):
                                                print(f"  Skills: {', '.join(map(str.strip, parsed_skills))}") # Join and strip each item
                                            else:
                                                print(f"  Skills (raw string): {skills}")
                                        except (ValueError, SyntaxError):
                                            print(f"  Skills (raw string, parsing failed): {skills}")
                                    elif isinstance(skills, list):
                                        print(f"  Skills: {', '.join(map(str.strip, skills))}") # Join and strip each item
                                    else:
                                        print(f"  Skills: {skills}") # Will print as is if not a list
                                    print("-" * 30)
                            else:
                                print(f"No Two-Tower recommendations generated for user '{sample_user_id}'.")

                            # Also test SBERT similarity for a text query
                            sample_query_text = "machine learning algorithms for data science"
                            print(f"\nRecommendations for text query: '{sample_query_text}' (using raw SBERT similarity):")
                            recommendations_sbert = recommender_trained.get_sbert_recommendations(query_text=sample_query_text, top_k=5)
                            if not recommendations_sbert.empty:
                                # Improved printing for SBERT recommendations
                                for i, row in recommendations_sbert.iterrows():
                                    print(f"  --- Recommendation {i+1} ---")
                                    print(f"  Title: {row.get('title', 'N/A')}")
                                    print(f"  SBERT Similarity Score: {row.get('sbert_similarity_score', 'N/A'):.4f}")
                                    print(f"  Adjusted Rating: {row.get('adjusted_rating', 'N/A'):.2f}")
                                    print(f"  Level: {row.get('level', 'N/A')}")
                                    # Ensure 'descrition' is used for description
                                    print(f"  Description: {row.get('descrition', 'N/A')}")
                                    print(f"  URL: {row.get('url', 'N/A')}")
                                    # Ensure skills_list is handled as a list for proper display
                                    skills = row.get('skills_list', 'N/A')
                                    # Check if skills is a string representation of a list, and try to parse it
                                    if isinstance(skills, str) and skills.startswith('[') and skills.endswith(']'):
                                        try:
                                            import ast
                                            parsed_skills = ast.literal_eval(skills)
                                            if isinstance(parsed_skills, list):
                                                print(f"  Skills: {', '.join(map(str.strip, parsed_skills))}") # Join and strip each item
                                            else:
                                                print(f"  Skills (raw string): {skills}")
                                        except (ValueError, SyntaxError):
                                            print(f"  Skills (raw string, parsing failed): {skills}")
                                    elif isinstance(skills, list):
                                        print(f"  Skills: {', '.join(map(str.strip, skills))}") # Join and strip each item
                                    else:
                                        print(f"  Skills: {skills}") # Will print as is if not a list
                                    print("-" * 30)
                            else:
                                print("No SBERT recommendations generated.")
                        else:
                            print("Cannot test recommendations: Data or pre-computed item embeddings are missing (after training).")

    print("\nTwo-Tower Recommender System execution finished.")
