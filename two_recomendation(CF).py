import tensorflow as tf
import tensorflow_recommenders as tfrs
import numpy as np
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import os
import sys
import random
from typing import Optional, Tuple, Dict, List

# Add parent directory for package import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

import config
import utils

def filter_positive_interactions(interactions_df: pd.DataFrame, rating_threshold: float = 3.5) -> pd.DataFrame:
    """
    Filters raw interactions to keep only positive ones.
    
    Args:
        interactions_df: DataFrame containing user interactions
        rating_threshold: Minimum rating value to consider as positive
        
    Returns:
        DataFrame containing only positive interactions
    """
    positive_mask = (
        (interactions_df['interaction_type'].isin(['click', 'like'])) |
        ((interactions_df['interaction_type'] == 'rating') & 
         (interactions_df['value'] >= rating_threshold))
    )
    return interactions_df[positive_mask][['user_id', 'item_id']]

class UserModel(tf.keras.Model):
    """Defines the user tower of the Two-Tower model."""
    def __init__(self, user_vocab: List[str], embedding_dim: int):
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

    def call(self, user_id: tf.Tensor) -> tf.Tensor:
        """Forward pass for the user tower."""
        return tf.nn.l2_normalize(self.user_embedding(user_id), axis=1)

class ItemModel(tf.keras.Model):
    """Defines the item (course) tower of the Two-Tower model."""
    def __init__(self, item_vocab: List[str], embedding_dim: int, item_content_embeddings: Optional[np.ndarray] = None):
        super().__init__()
        self.item_vocab_size = len(item_vocab) + 1
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
        self.final_projection = tf.keras.Sequential([
            tf.keras.layers.Dense(config.TWO_TOWER_SHARED_EMBEDDING_DIM, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(config.TWO_TOWER_SHARED_EMBEDDING_DIM)
        ])

    def call(self, item_id: tf.Tensor) -> tf.Tensor:
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

class TwoTowerModel(tfrs.Model):
    """The main Two-Tower model integrating user and item towers."""
    def __init__(self, user_model: UserModel, item_model: ItemModel, 
                 item_ids_vocab: List[str], item_dataset: tf.data.Dataset,
                 item_titles_map: Dict[str, str]):
        super().__init__()
        self.user_model = user_model
        self.item_model = item_model
        self.item_ids_vocab = tf.constant(item_ids_vocab)
        self.item_titles_map = item_titles_map
        self.item_dataset = item_dataset

        try:
            # Prepare candidates dataset
            candidate_embeddings_dataset = self.item_dataset.batch(128).map(self.item_model)
            
            # Initialize retrieval metrics with correct parameters
            self.retrieval_metrics = tfrs.metrics.FactorizedTopK(
                candidates=candidate_embeddings_dataset
            )
            print("TwoTowerModel: Initialized FactorizedTopK metric with candidate embeddings dataset.")
            
            # Initialize retrieval task with cosine similarity
            self.task = tfrs.tasks.Retrieval(
                metrics=self.retrieval_metrics,
                temperature=0.1  # Lower temperature for sharper predictions
            )
            print("TwoTowerModel: Initialized tfrs.tasks.Retrieval.")
        except Exception as e:
            print(f"ERROR during FactorizedTopK/Retrieval initialization: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def compute_loss(self, features: Dict[str, tf.Tensor], training: bool = False) -> tf.Tensor:
        """Computes the loss for a batch of features."""
        user_embeddings = self.user_model(features["user_id"])
        item_embeddings = self.item_model(features["item_id"])

        # Normalize embeddings for better cosine similarity
        user_embeddings = tf.nn.l2_normalize(user_embeddings, axis=1)
        item_embeddings = tf.nn.l2_normalize(item_embeddings, axis=1)

        return self.task(
            user_embeddings, 
            item_embeddings, 
            compute_metrics=not training
        )

class TwoTowerRecommender:
    """Handles the setup, training, and prediction for the Two-Tower model."""
    def __init__(self, courses_df: pd.DataFrame, user_interactions_df: pd.DataFrame, 
                 model_weights_path: Optional[str] = None):
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

        # Load SBERT model for content-based recommendations
        self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("SBERT model 'all-MiniLM-L6-v2' loaded for content-based recommendations.")

    def _load_item_content_embeddings(self) -> None:
        """Load pre-computed SBERT embeddings for course content."""
        try:
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

    def _prepare_vocabularies(self) -> None:
        """Creates unique vocabularies for users and items."""
        print("Preparing vocabularies and maps...")
        print(f"DEBUG: courses_df['item_id'] dtype: {self.courses_df['item_id'].dtype}")
        print(f"DEBUG: Sample courses_df['item_id'] values: {self.courses_df['item_id'].head().tolist()}")

        self.user_vocab = self.user_interactions_df["user_id"].unique().tolist()
        self.item_vocab = self.courses_df["item_id"].tolist()
        print(f"Item vocabulary size (unique IDs): {len(set(self.item_vocab))}")
        print(f"User vocabulary size: {len(self.user_vocab)}")
        
        self.item_titles_map = pd.Series(
            self.courses_df["title"].values, 
            index=self.courses_df["item_id"]
        ).to_dict()

    def _build_model(self) -> Optional[TwoTowerModel]:
        """Builds the Keras TwoTowerModel structure."""
        print("Building Two-Tower Keras model...")
        if not self.user_vocab or not self.item_vocab:
            print("Error: Vocabularies not prepared. Cannot build model.")
            return None
            
        # Create user model
        user_model = UserModel(
            self.user_vocab, 
            config.TWO_TOWER_SHARED_EMBEDDING_DIM
        )
        
        # Check SBERT embeddings alignment
        if self.course_embeddings is not None:
            if len(self.course_embeddings) != len(self.item_vocab):
                print(f"Warning: Number of SBERT embeddings ({len(self.course_embeddings)}) does not match number of courses ({len(self.item_vocab)}). Using only learned embeddings.")
                self.course_embeddings = None
            else:
                print(f"Using SBERT embeddings with shape: {self.course_embeddings.shape}")
        else:
            print("No SBERT embeddings available. Using only learned embeddings.")

        # Create item model
        item_model = ItemModel(
            item_vocab=self.item_vocab,
            embedding_dim=config.TWO_TOWER_ITEM_EMBEDDING_DIM,
            item_content_embeddings=self.course_embeddings
        )
            
        # Prepare item dataset for candidates
        item_dataset_for_candidates = tf.data.Dataset.from_tensor_slices(
            tf.constant(self.item_vocab)
        )

        try:
            model = TwoTowerModel(
                user_model=user_model,
                item_model=item_model,
                item_ids_vocab=self.item_vocab,
                item_dataset=item_dataset_for_candidates,
                item_titles_map=self.item_titles_map
            )
            print("Two-Tower Keras model built successfully.")
            return model
        except Exception as e:
            print(f"Error building Two-Tower model: {e}")
            import traceback
            traceback.print_exc()
            return None

    def prepare_data_for_training(self) -> Tuple[Optional[tf.data.Dataset], Optional[tf.data.Dataset]]:
        """Converts interaction data into TensorFlow Datasets for training."""
        if self.user_interactions_df is None or self.user_interactions_df.empty:
            print("Error: No interaction data available for training.")
            return None, None
            
        # Create dataset from interactions
        interactions_dict = {
            "user_id": np.array(self.user_interactions_df["user_id"]),
            "item_id": np.array(self.user_interactions_df["item_id"])
        }
        dataset = tf.data.Dataset.from_tensor_slices(interactions_dict)

        # Shuffle and split data
        tf.random.set_seed(42)
        shuffled = dataset.shuffle(
            len(self.user_interactions_df), 
            seed=42, 
            reshuffle_each_iteration=False
        )

        train_size = int(len(self.user_interactions_df) * (1 - config.TWO_TOWER_TEST_SPLIT))
        train_dataset = shuffled.take(train_size)
        test_dataset = shuffled.skip(train_size)

        # Batch and cache datasets
        train_dataset = train_dataset.batch(config.TWO_TOWER_BATCH_SIZE).cache()
        test_dataset = test_dataset.batch(config.TWO_TOWER_BATCH_SIZE).cache()
            
        print(f"Training dataset size: {train_size} interactions.")
        print(f"Test dataset size: {len(self.user_interactions_df) - train_size} interactions.")
        return train_dataset, test_dataset

    def compile_model(self) -> None:
        """Compiles the Keras model with optimizer."""
        if self.model is None:
            print("Error: Model not built. Cannot compile.")
            return
        self.model.compile(
            optimizer=tf.keras.optimizers.Adagrad(
                learning_rate=config.TWO_TOWER_LEARNING_RATE
            )
        )
        print("Model compiled.")

    def _precompute_item_embeddings(self) -> bool:
        """Pre-computes item embeddings using the trained model."""
        if self.model is None:
            print("Error: Model not available. Cannot pre-compute embeddings.")
            return False
            
        try:
            # Create tensor of all item_ids
            all_item_ids_tensor = tf.constant(self.item_vocab)
            
            # Get embeddings from item model
            self.item_embeddings_precomputed = self.model.item_model(all_item_ids_tensor)
            
            # Normalize embeddings
            self.item_embeddings_norm = tf.nn.l2_normalize(
                self.item_embeddings_precomputed, 
                axis=1
            )
            
            print("Successfully pre-computed item embeddings.")
            return True
        except Exception as e:
            print(f"Error pre-computing item embeddings: {e}")
            import traceback
            traceback.print_exc()
            return False

    def train_model(self, train_dataset: tf.data.Dataset, 
                   test_dataset: tf.data.Dataset) -> Optional[tf.keras.callbacks.History]:
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

    def save_model_weights(self) -> None:
        """Saves the trained model weights."""
        if self.model is None:
            print("Error: No model to save.")
            return
        try:
            os.makedirs(
                os.path.dirname(config.TWO_TOWER_MODEL_WEIGHTS_PATH), 
                exist_ok=True
            )
            self.model.save_weights(config.TWO_TOWER_MODEL_WEIGHTS_PATH)
            print(f"Model weights saved successfully to {config.TWO_TOWER_MODEL_WEIGHTS_PATH}")
        except Exception as e:
            print(f"Error saving model weights: {e}")

    def load_model_weights(self) -> bool:
        """Loads pre-trained model weights."""
        if self.model is None:
            print("Model structure not built. Attempting to build...")
            self._build_model()
            if self.model is None:
                print("Failed to build model structure. Cannot load weights.")
                return False
            print("Model structure built.")

        if not os.path.exists(config.TWO_TOWER_MODEL_WEIGHTS_PATH):
            print(f"Error: Model weights file not found at {config.TWO_TOWER_MODEL_WEIGHTS_PATH}")
            return False
            
        try:
            # Run dummy forward pass to build layers
            dummy_user_id_val = self.user_vocab[0] if self.user_vocab else "dummy_user_0"
            dummy_item_id_val = self.item_vocab[0] if self.item_vocab else "dummy_item_0"
            dummy_input = {
                "user_id": tf.constant([dummy_user_id_val]),
                "item_id": tf.constant([dummy_item_id_val])
            }
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

    def get_recommendations(self, user_id: str, top_k: int = 10) -> pd.DataFrame:
        """Generates top_k recommendations for a given user_id."""
        if self.model is None or self.item_embeddings_precomputed is None:
            print("Model not available or item embeddings not pre-computed. Attempting to load weights and re-compute...")
            if not self.load_model_weights():
                print("Failed to load model weights. Cannot generate recommendations.")
                return pd.DataFrame()
            print("Model weights loaded and item embeddings pre-computed.")
                
        if user_id not in self.user_vocab:
            print(f"Warning: User ID '{user_id}' not found in training data vocabulary.")
            return pd.DataFrame()

        # Get user embedding
        user_embedding = self.model.user_model(tf.constant([user_id]))
        
        # Compute similarity scores
        similarity_scores = tf.matmul(
            user_embedding, 
            self.item_embeddings_norm, 
            transpose_b=True
        )
        similarity_scores = tf.squeeze(similarity_scores, axis=0)
        
        # Get top-k recommendations
        top_scores, top_indices = tf.math.top_k(
            similarity_scores, 
            k=min(top_k, len(self.item_vocab))
        )
        
        # Create recommendations DataFrame
        recommended_item_ids = [self.item_vocab[idx] for idx in top_indices.numpy()]
        recommended_scores = top_scores.numpy()

        # Create initial recommendations DataFrame
        recommendations_df = pd.DataFrame({
            'item_id': recommended_item_ids,
            'similarity_score': recommended_scores
        })
        
        # Merge with course details
        final_recommendations = pd.merge(
            recommendations_df,
            self.courses_df,
            on='item_id',
            how='left'
        )
        
        # Ensure all required columns exist
        required_columns = ['title', 'similarity_score', 'adjusted_rating', 'level', 'url', 'skills_list']
        for col in required_columns:
            if col not in final_recommendations.columns:
                if col == 'title':
                    final_recommendations['title'] = final_recommendations['item_id']
                elif col == 'similarity_score':
                    continue  # Already exists
                else:
                    final_recommendings[col] = 'N/A'
        
        # Select and reorder columns
        output_columns = ['title', 'similarity_score', 'adjusted_rating', 'level', 'url', 'skills_list']
        final_recommendations = final_recommendations[output_columns]
        
        # Convert skills_list to string if it's a list
        if 'skills_list' in final_recommendations.columns:
            final_recommendations['skills_list'] = final_recommendations['skills_list'].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else str(x)
            )
        
        return final_recommendations

    def get_sbert_recommendations(self, query_text: str, top_k: int = 5) -> pd.DataFrame:
        """Generates content-based recommendations using SBERT embeddings."""
        if self.course_embeddings is None:
            print("Error: Course SBERT embeddings not available.")
            return pd.DataFrame()

        # Encode query
        query_embedding = self.sbert_model.encode(
            query_text, 
            convert_to_tensor=True
        )
        
        # Compute similarities
        similarities = util.pytorch_cos_sim(
            query_embedding.unsqueeze(0), 
            torch.from_numpy(self.course_embeddings)
        )[0]
        
        # Get top-k indices
        top_indices = similarities.argsort(descending=True)[:top_k]
        
        # Create recommendations DataFrame
        recommended_item_ids = [self.item_vocab[idx] for idx in top_indices]
        recommended_scores = similarities[top_indices].numpy()

        recommendations_df = pd.DataFrame({
            'item_id': recommended_item_ids,
            'title': [self.item_titles_map.get(item_id, "Unknown Title") for item_id in recommended_item_ids],
            'similarity_score': recommended_scores
        })
        
        # Debug prints
        print("\nDEBUG: SBERT recommendations_df before merge:")
        print(f"  item_id dtype: {recommendations_df['item_id'].dtype}")
        print(f"  Sample item_id values: {recommendations_df['item_id'].head().tolist()}")
        print(f"DEBUG: courses_df_loaded (self.courses_df) before merge:")
        print(f"  item_id dtype: {self.courses_df['item_id'].dtype}")
        print(f"  Sample item_id values: {self.courses_df['item_id'].head().tolist()}")
        print("-" * 50)

        # Merge with course details
        final_recommendations = recommendations_df.merge(
            self.courses_df, 
            on='item_id', 
            how='left'
        )
        
        # Select output columns
        output_cols = [
            'title', 'similarity_score', 'adjusted_rating', 
            'level', 'descrition', 'url', 'skills_list'
        ]
        existing_output_cols = [
            col for col in output_cols 
            if col in final_recommendations.columns
        ]

        return final_recommendations[existing_output_cols]

if __name__ == "__main__":
    try:
        # Load course data
        courses_df = utils.load_course_data(config.COURSE_DATA_PATH)
        if courses_df is None or courses_df.empty:
            raise ValueError("Failed to load course data or data is empty")

        # Load user interactions
        try:
            raw_user_interactions_df = pd.read_csv(
                config.INTERACTION_DATA_PATH,
                encoding='utf-8'
            )
        except FileNotFoundError:
            print(f"Error: Interaction data file not found at {config.INTERACTION_DATA_PATH}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading interaction data: {e}")
            sys.exit(1)

        if raw_user_interactions_df.empty:
            print("Error: Interaction data is empty")
            sys.exit(1)

        # Filter to positive interactions
        positive_user_interactions_df = filter_positive_interactions(raw_user_interactions_df)
        if positive_user_interactions_df.empty:
            print("Error: No positive interactions found after filtering")
            sys.exit(1)

        # Initialize recommender
        recommender = TwoTowerRecommender(
            courses_df=courses_df,
            user_interactions_df=positive_user_interactions_df
        )

        # Prepare training data
        train_dataset, test_dataset = recommender.prepare_data_for_training()
        if train_dataset is None or test_dataset is None:
            print("Error: Failed to prepare training data")
            sys.exit(1)

        # Compile and train model
        recommender.compile_model()
        history = recommender.train_model(train_dataset, test_dataset)
        if history is None:
            print("Error: Model training failed")
            sys.exit(1)

        # Save model weights
        recommender.save_model_weights()

        # Re-initialize with trained weights
        recommender_trained = TwoTowerRecommender(
            courses_df=courses_df,
            user_interactions_df=positive_user_interactions_df,
            model_weights_path=config.TWO_TOWER_MODEL_WEIGHTS_PATH
        )

        # Test recommendations
        if recommender_trained.courses_df is not None and recommender_trained.item_embeddings_norm is not None:
            # Get sample user
            if not positive_user_interactions_df.empty:
                sample_user_id = random.choice(positive_user_interactions_df['user_id'].tolist())
            else:
                sample_user_id = "user_0"
                print(f"Warning: No positive interactions to sample from. Using default user_id: {sample_user_id}")

            # Get Two-Tower recommendations
            print(f"\nRecommendations for User: '{sample_user_id}' (using Two-Tower Model):")
            recommendations_tt = recommender_trained.get_recommendations(
                user_id=sample_user_id, 
                top_k=5
            )
            print(recommendations_tt)

            # Get SBERT recommendations
            sample_query = "machine learning algorithms for data science"
            print(f"\nContent-based recommendations for query: '{sample_query}' (using SBERT):")
            recommendations_sbert = recommender_trained.get_sbert_recommendations(
                query_text=sample_query, 
                top_k=5
            )
            print(recommendations_sbert)

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 