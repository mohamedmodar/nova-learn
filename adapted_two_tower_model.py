import tensorflow as tf
import numpy as np
from tensorflow.keras import layers, Model
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch

# Constants
SBERT_EMBEDDING_DIM = 384  # Dimension of our SBERT embeddings
SHARED_EMBEDDING_DIM = 64  # Final embedding dimension for both towers

class UserTower(layers.Layer):
    def __init__(self, vector_dim):
        super().__init__()
        self.dense = tf.keras.Sequential([
            layers.Dense(2 * vector_dim, activation="relu", name='user_dense1'),
            layers.Dense(128, activation='relu', name='user_dense2'),
            layers.Dense(SHARED_EMBEDDING_DIM, name='user_dense3')
        ])
    
    def call(self, inputs):
        # For our adaptation, we'll use the query embedding as the main input
        # and a context vector (which could be derived from filters) as the secondary input
        query_embedding, context_vector = inputs
        concatenated = tf.concat([query_embedding, context_vector], axis=-1)
        return self.dense(concatenated)

class ItemTower(layers.Layer):
    def __init__(self, vector_dim):
        super().__init__()
        self.dense = tf.keras.Sequential([
            layers.Dense(vector_dim, activation="relu", name='item_dense1'),
            layers.Dense(SHARED_EMBEDDING_DIM, name='item_dense2')
        ])
    
    def call(self, item_embedding):
        return self.dense(item_embedding)

class TwoTowerModel(Model):
    def __init__(self, vector_dim):
        super(TwoTowerModel, self).__init__()
        self.user_tower = UserTower(vector_dim)
        self.item_tower = ItemTower(vector_dim)
        self.cosine_similarity = layers.Dot(axes=-1, normalize=True)
        
    def call(self, inputs):
        # Unpack the input components
        query_embedding, context_vector, item_embedding = inputs
        
        # Process through towers
        user_embedding = self.user_tower([query_embedding, context_vector])
        item_embedding = self.item_tower(item_embedding)
        
        # Calculate similarity
        return self.cosine_similarity([user_embedding, item_embedding])
    
    def get_user_embedding(self, query_embedding, context_vector):
        """Get the user embedding for a given query and context"""
        return self.user_tower([query_embedding, context_vector])
    
    def get_item_embedding(self, item_embedding):
        """Get the item embedding for a given course embedding"""
        return self.item_tower(item_embedding)

class CourseRecommender:
    def __init__(self, model_path=None):
        """Initialize the recommender with a trained model and course data"""
        # Load SBERT model for encoding queries
        self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("SBERT model loaded successfully")
        
        # Load course data and embeddings
        self.load_course_data()
        
        # Get embedding dimension from loaded data
        if self.course_embeddings is not None:
            vector_dim = self.course_embeddings.shape[1]
        else:
            vector_dim = SBERT_EMBEDDING_DIM
            
        # Initialize the model
        self.model = TwoTowerModel(vector_dim)
        
        # Initialize with dummy data to build the model
        dummy_query = tf.zeros((1, vector_dim))
        dummy_context = tf.zeros((1, vector_dim))
        dummy_item = tf.zeros((1, vector_dim))
        _ = self.model((dummy_query, dummy_context, dummy_item))
        
        # Load pre-trained weights if provided
        if model_path:
            try:
                self.model.load_weights(model_path)
                print(f"Loaded model weights from {model_path}")
                
                # Pre-compute item embeddings
                self.item_embeddings = self.model.get_item_embedding(self.course_embeddings)
                self.item_embeddings_norm = tf.nn.l2_normalize(self.item_embeddings, axis=-1)
                print("Pre-computed normalized item embeddings")
            except Exception as e:
                print(f"Error loading model weights: {e}")
        
    def load_course_data(self):
        """Load course data and pre-compute item embeddings"""
        try:
            # Load course data
            self.courses_df = pd.read_csv('cleaned_courses_with_enhanced_skills.csv')
            print(f"Loaded course data with shape: {self.courses_df.shape}")
            
            # Process skills_list column if it exists
            if 'skills_list' in self.courses_df.columns:
                self.courses_df['skills_list'] = self.courses_df['skills_list'].apply(
                    lambda x: eval(x) if isinstance(x, str) and x.startswith("[") else ([] if pd.isna(x) else [x])
                )
            
            # Load SBERT embeddings
            with open('course_sbert_embeddings.pkl', 'rb') as f:
                course_embeddings = pickle.load(f)
            
            # Convert to TensorFlow tensor
            self.course_embeddings = tf.convert_to_tensor(course_embeddings, dtype=tf.float32)
            print(f"Loaded course embeddings with shape: {self.course_embeddings.shape}")
            
        except Exception as e:
            print(f"Error loading course data: {e}")
            self.courses_df = None
            self.course_embeddings = None
            self.item_embeddings = None
            self.item_embeddings_norm = None
    
    def get_sbert_recommendations(self, query_text, top_k=5):
        """Get recommendations using raw SBERT embeddings"""
        if not query_text or not isinstance(query_text, str):
            print("Error: Query text must be a non-empty string.")
            return pd.DataFrame()
            
        try:
            # Generate embedding for the query text
            query_embedding = self.sbert_model.encode(query_text, convert_to_tensor=True)
            
            # Convert course embeddings to PyTorch tensor if needed
            if not isinstance(self.course_embeddings, torch.Tensor):
                course_embeddings_tensor = torch.tensor(self.course_embeddings.numpy())
            else:
                course_embeddings_tensor = self.course_embeddings
            
            # Compute cosine similarity
            cosine_scores = util.cos_sim(query_embedding, course_embeddings_tensor)[0]
            
            # Get top-k scores and indices
            top_results = torch.topk(cosine_scores, k=min(top_k, len(cosine_scores)))
            top_indices = top_results.indices.tolist()
            top_scores = top_results.values.tolist()
            
            # Create recommendations DataFrame
            recommendations = self.courses_df.iloc[top_indices].copy()
            recommendations['sbert_similarity_score'] = top_scores
            
            # Select and order columns
            output_columns = ['title', 'provider', 'url', 'level', 'skills', 'adjusted_rating', 'duration', 'sbert_similarity_score']
            return recommendations[output_columns]
            
        except Exception as e:
            print(f"Error generating SBERT recommendations: {e}")
            return pd.DataFrame()
    
    def recommend(self, query_text=None, context_vector=None, top_k=5):
        """
        Recommend courses based on a query text and optional context
        
        Args:
            query_text: Text query to encode and use for recommendations
            context_vector: Optional context vector (e.g., from filters)
            top_k: Number of recommendations to return
            
        Returns:
            DataFrame with top_k recommended courses
        """
        if self.courses_df is None or self.course_embeddings is None:
            print("Course data not loaded. Cannot make recommendations.")
            return pd.DataFrame()
        
        # Generate query embedding if text is provided
        if query_text:
            query_embedding = self.sbert_model.encode([query_text])[0]
            query_embedding = tf.convert_to_tensor([query_embedding], dtype=tf.float32)
        else:
            # Use a default query if none provided
            query_embedding = tf.zeros((1, self.course_embeddings.shape[1]))
        
        # Create default context vector if none provided
        if context_vector is None:
            context_vector = tf.zeros((1, self.course_embeddings.shape[1]))
        elif len(context_vector.shape) == 1:
            context_vector = tf.expand_dims(context_vector, axis=0)
        
        # Get user embedding
        user_embedding = self.model.get_user_embedding(query_embedding, context_vector)
        user_embedding_norm = tf.nn.l2_normalize(user_embedding, axis=-1)
        
        # Compute similarity with all item embeddings
        similarity_scores = tf.matmul(user_embedding_norm, self.item_embeddings_norm, transpose_b=True)
        similarity_scores = tf.squeeze(similarity_scores, axis=0)
        
        # Get top-k indices and scores
        top_scores, top_indices = tf.math.top_k(similarity_scores, k=top_k)
        
        # Convert to numpy for easier handling
        top_indices_np = top_indices.numpy()
        top_scores_np = top_scores.numpy()
        
        # Create recommendations DataFrame
        recommendations = self.courses_df.iloc[top_indices_np].copy()
        recommendations['similarity_score'] = top_scores_np
        
        # Ensure we only return columns that exist
        return_columns = ['title', 'provider', 'level', 'adjusted_rating', 'similarity_score', 'url']
        # Add skills_list if it exists
        if 'skills_list' in recommendations.columns:
            return_columns.insert(3, 'skills_list')
            
        return recommendations[return_columns]

def generate_training_pairs(course_embeddings, batch_size=1024, num_batches=100):
    """
    Generate synthetic training data for the two-tower model.
    
    This function creates pairs of (query, context, item) with target similarity scores.
    The synthetic queries are created by combining course embeddings with noise.
    
    Args:
        course_embeddings: Tensor of course SBERT embeddings
        batch_size: Number of examples per batch
        num_batches: Number of batches to generate
        
    Yields:
        Tuple of ((query, context, item), target) for training
    """
    n = course_embeddings.shape[0]
    embedding_dim = course_embeddings.shape[1]
    
    for _ in range(num_batches):
        # Randomly sample course indices
        indices = np.random.randint(0, n, size=(batch_size, 3))
        
        # Get course embeddings for these indices
        course1 = tf.gather(course_embeddings, indices[:, 0])
        course2 = tf.gather(course_embeddings, indices[:, 1])
        item = tf.gather(course_embeddings, indices[:, 2])
        
        # Create synthetic query by combining course1 and course2
        # This simulates a query that is related to both courses
        query = 0.7 * course1 + 0.3 * course2 + 0.05 * tf.random.normal((batch_size, embedding_dim))
        
        # Create a simple context vector (could be more sophisticated)
        context = 0.2 * course1 + 0.1 * tf.random.normal((batch_size, embedding_dim))
        
        # Normalize vectors
        query = tf.nn.l2_normalize(query, axis=1)
        context = tf.nn.l2_normalize(context, axis=1)
        
        # Calculate target similarity based on relationship between query and item
        # Higher similarity for items that are related to course1 (main component of query)
        cos_sim = tf.keras.layers.Dot(axes=-1, normalize=True)
        target = cos_sim([course1, item])
        target = tf.reshape(target, [-1, 1])  # Shape: (batch_size, 1)
        
        yield (query, context, item), target

def train_two_tower_model(model, course_embeddings, epochs=10, steps_per_epoch=100, batch_size=1024, save_path='two_tower.weights.h5'):
    """
    Train the two-tower model using synthetic data generated from course embeddings.
    
    Args:
        model: The TwoTowerModel instance
        course_embeddings: Tensor of course SBERT embeddings
        epochs: Number of training epochs
        steps_per_epoch: Number of steps per epoch
        batch_size: Batch size for training
        save_path: Path to save the best model weights
        
    Returns:
        Training history
    """
    # Compile the model
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    
    # Create dataset from generator
    dataset = tf.data.Dataset.from_generator(
        lambda: generate_training_pairs(course_embeddings, batch_size, steps_per_epoch * epochs),
        output_signature=(
            (
                tf.TensorSpec(shape=(None, course_embeddings.shape[1]), dtype=tf.float32),
                tf.TensorSpec(shape=(None, course_embeddings.shape[1]), dtype=tf.float32),
                tf.TensorSpec(shape=(None, course_embeddings.shape[1]), dtype=tf.float32)
            ),
            tf.TensorSpec(shape=(None, 1), dtype=tf.float32)
        )
    )
    
    # Set up checkpoint callback to save best model
    checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        save_path,
        monitor='loss',
        save_best_only=True,
        save_weights_only=True,
        verbose=1
    )
    
    # Train the model
    history = model.fit(
        dataset,
        steps_per_epoch=steps_per_epoch,
        epochs=epochs,
        callbacks=[checkpoint_callback]
    )
    
    return history
