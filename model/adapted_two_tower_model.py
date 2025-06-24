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
MAX_HISTORY_LENGTH = 20 # Max user interaction history to consider

class UserTower(layers.Layer):
    """
    A simple tower for user features. For content-based tasks, this can process
    an embedding derived from a text query or averaged history.
    This is the restored, simpler version of the tower.
    """
    def __init__(self, name="UserTower", **kwargs):
        super().__init__(name=name, **kwargs)
        self.dense = tf.keras.Sequential([
            layers.Dense(256, activation='relu', name='user_dense1'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(128, activation='relu', name='user_dense2'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(SHARED_EMBEDDING_DIM, name='user_dense3')
        ])

    def call(self, user_input, training=False):
        """Processes a single user embedding tensor."""
        return self.dense(user_input, training=training)

class QueryTower(layers.Layer):
    """A tower to process a single text query embedding."""
    def __init__(self, name="QueryTower", **kwargs):
        super().__init__(name=name, **kwargs)
        self.dense = tf.keras.Sequential([
            layers.Dense(256, activation='relu', name='query_dense1'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(128, activation='relu', name='query_dense2'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(SHARED_EMBEDDING_DIM, name='query_dense3')
        ])

    def call(self, query_embedding, training=False):
        return self.dense(query_embedding, training=training)

class ItemTower(layers.Layer):
    """A tower for course representations."""
    def __init__(self, vector_dim):
        super().__init__()
        self.dense = tf.keras.Sequential([
            layers.Dense(vector_dim, activation="relu", name='item_dense1'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(128, activation='relu', name='item_dense2'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(SHARED_EMBEDDING_DIM, name='item_dense3')
        ])
    
    def call(self, item_embedding, training=False):
        return self.dense(item_embedding, training=training)

class TwoTowerModel(Model):
    def __init__(self, vector_dim):
        super(TwoTowerModel, self).__init__()
        # Both user and query towers are available for different use cases.
        # For our new training, we will focus on the QueryTower.
        self.user_tower = UserTower()
        self.query_tower = QueryTower()
        self.item_tower = ItemTower(vector_dim)
        self.cosine_similarity = layers.Dot(axes=-1, normalize=True)
        
    def call(self, inputs, training=False):
        """
        This call is for INFERENCE. It expects a single query embedding and an item embedding.
        The user_tower is not used here but is available.
        """
        query_input, item_candidate_embedding = inputs
        query_embedding = self.query_tower(query_input, training=training)
        item_embedding = self.item_tower(item_candidate_embedding, training=training)
        return self.cosine_similarity([query_embedding, item_embedding])

    def train_step(self, data):
        """
        Custom training step using triplet loss, focused on CONTENT.
        It learns to map a course's text (via QueryTower) to its own embedding (via ItemTower).
        """
        # Unpack the data: anchor is text, positive/negative are item embeddings
        anchor_text_embedding, positive_item_embedding, negative_item_embedding = data

        with tf.GradientTape() as tape:
            # Get embeddings from the appropriate towers
            query_vector = self.query_tower(anchor_text_embedding, training=True)
            positive_vector = self.item_tower(positive_item_embedding, training=True)
            negative_vector = self.item_tower(negative_item_embedding, training=True)

            # Calculate triplet loss
            pos_sim = self.cosine_similarity([query_vector, positive_vector])
            neg_sim = self.cosine_similarity([query_vector, negative_vector])
            
            margin = 0.1
            loss = tf.reduce_mean(tf.maximum(0., neg_sim - pos_sim + margin))

        # Apply gradients
        # Note: We only train the query_tower and item_tower here. user_tower is untouched.
        trainable_vars = self.query_tower.trainable_variables + self.item_tower.trainable_variables
        gradients = tape.gradient(loss, trainable_vars)
        self.optimizer.apply_gradients(zip(gradients, trainable_vars))

        return {'loss': loss}
    
    def get_user_embedding(self, user_query_embedding):
        """Get the user/query embedding for a given text query SBERT embedding"""
        return self.query_tower(user_query_embedding)
    
    def get_item_embedding(self, item_embedding):
        """Get the item embedding for a given course SBERT embedding"""
        return self.item_tower(item_embedding)

class CourseRecommender:
    """
    This class now primarily serves to load a trained Two-Tower model and
    provides methods to get embeddings. The recommendation logic itself
    has been moved to the main recommender interface for better cohesion.
    """
    def __init__(self, courses_df, course_sbert_embeddings, model_path=None):
        self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.courses_df = courses_df
        self.course_embeddings = course_sbert_embeddings
        
        vector_dim = self.course_embeddings.shape[1]
        self.model = TwoTowerModel(vector_dim)
        
        # Build the model with dummy data
        dummy_query = tf.zeros((1, SBERT_EMBEDDING_DIM))
        dummy_item = tf.zeros((1, vector_dim))
        _ = self.model((dummy_query, dummy_item))
        
        self.item_embeddings_norm = None
        if model_path:
            try:
                self.model.load_weights(model_path)
                print(f"Loaded model weights from {model_path}")
                # Pre-compute item embeddings
                self.item_embeddings = self.model.get_item_embedding(self.course_embeddings)
                self.item_embeddings_norm = tf.nn.l2_normalize(self.item_embeddings, axis=-1)
                print("Pre-computed normalized item embeddings.")
            except Exception as e:
                print(f"Error loading model weights for CourseRecommender: {e}")
        else:
            print("No model path provided to CourseRecommender.")

    def recommend(self, query_text, top_k=5):
        """
        Simplified recommendation based on a text query.
        This uses the trained QueryTower.
        """
        if self.item_embeddings_norm is None:
            print("Model not loaded, cannot provide Two-Tower recommendations.")
            return pd.DataFrame()

        query_embedding = self.sbert_model.encode(query_text, convert_to_tensor=True)
        query_embedding_tf = tf.expand_dims(tf.convert_to_tensor(query_embedding.numpy()), axis=0)

        user_vector = self.model.get_user_embedding(query_embedding_tf)
        user_vector_norm = tf.nn.l2_normalize(user_vector, axis=-1)
        
        similarity_scores = tf.matmul(user_vector_norm, self.item_embeddings_norm, transpose_b=True)
        similarity_scores = tf.squeeze(similarity_scores, axis=0)
        
        top_scores, top_indices = tf.math.top_k(similarity_scores, k=top_k)
        
        recommendations = self.courses_df.iloc[top_indices.numpy()].copy()
        recommendations['similarity_score'] = top_scores.numpy()
        
        return recommendations[['title', 'provider', 'level', 'similarity_score', 'url']]

def create_content_dataset(batch_size=1024):
    """
    Creates a tf.data.Dataset from course content for training the Two-Tower model.
    Yields triplets of (anchor_text_embedding, positive_item_embedding, negative_item_embedding).
    """
    print("--- Creating Content-Based Dataset ---")
    try:
        courses_df = pd.read_csv('data/final(final).csv')
        with open('models/course_sbert_embeddings.pkl', 'rb') as f:
            course_embeddings = pickle.load(f)
        course_embeddings = tf.convert_to_tensor(course_embeddings, dtype=tf.float32)
        print(f"Loaded {len(courses_df)} courses and their embeddings.")
    except Exception as e:
        print(f"Error loading data for dataset creation: {e}")
        return None
    
    # Pre-encode all course texts (title + description)
    print("Preprocessing and encoding all course texts for training...")
    sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
    courses_df['text'] = courses_df['title'].fillna('') + ' ' + courses_df['description'].fillna('')
    text_embeddings = sbert_model.encode(courses_df['text'].tolist(), show_progress_bar=True, convert_to_tensor=True)
    text_embeddings_tf = tf.convert_to_tensor(text_embeddings.numpy(), dtype=tf.float32)
    print(f"Encoded all texts. Shape: {text_embeddings_tf.shape}")

    total_courses = len(courses_df)

    def generator():
        """A generator function that yields training samples."""
        for i in range(total_courses):
            anchor_text_emb = text_embeddings_tf[i]
            positive_item_emb = course_embeddings[i]
            
            # Sample a random negative item
            while True:
                negative_idx = np.random.randint(0, total_courses)
                if negative_idx != i:
                    break
            
            negative_item_emb = course_embeddings[negative_idx]
            yield (anchor_text_emb, positive_item_emb, negative_item_emb)

    dataset = tf.data.Dataset.from_generator(
        generator,
        output_signature=(
            tf.TensorSpec(shape=(SBERT_EMBEDDING_DIM,), dtype=tf.float32),
            tf.TensorSpec(shape=(SBERT_EMBEDDING_DIM,), dtype=tf.float32),
            tf.TensorSpec(shape=(SBERT_EMBEDDING_DIM,), dtype=tf.float32)
        )
    )
    
    return dataset.shuffle(10000).batch(batch_size).prefetch(tf.data.AUTOTUNE)

def train_content_based_model(model, epochs=10, batch_size=1024, save_path='models/two_tower_content_based.weights.h5'):
    """
    Train the two-tower model using course content.
    """
    dataset = create_content_dataset(batch_size)
    if dataset is None:
        print("Could not create dataset. Aborting training.")
        return None

    # We are training the QueryTower and ItemTower. The UserTower is not trained here.
    model.user_tower.trainable = False

    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001))
    
    checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        save_path,
        monitor='loss',
        save_best_only=True,
        save_weights_only=True,
        verbose=1
    )
    
    print("\nStarting training of CONTENT-BASED Two-Tower model...")
    history = model.fit(
        dataset,
        epochs=epochs,
        callbacks=[checkpoint_callback]
    )
    
    print("Training finished.")
    model.user_tower.trainable = True # Unfreeze for potential other uses
    return history

if __name__ == "__main__":
    print("--- Running Content-Based Two-Tower Model Training Script ---")
    
    try:
        with open('models/course_sbert_embeddings.pkl', 'rb') as f:
            course_embeddings = pickle.load(f)
        embedding_dim = course_embeddings.shape[1]
    except FileNotFoundError:
        print("❌ Error: SBERT embeddings not found. Please run embedding generation first.")
        exit()

    print("\nInstantiating the Two-Tower Model...")
    two_tower_model = TwoTowerModel(vector_dim=embedding_dim)
    
    # Dummy call to build model layers
    dummy_query = tf.zeros((1, SBERT_EMBEDDING_DIM))
    dummy_item = tf.zeros((1, embedding_dim))
    _ = two_tower_model((dummy_query, dummy_item))
    print("✅ Model instantiated.")
    
    print("\nStarting the training process...")
    training_history = train_content_based_model(
        two_tower_model, 
        epochs=15,
        batch_size=512
    )
    
    if training_history:
        print("\n--- ✅ Training Complete ---")
        print("Model weights have been saved to 'models/two_tower_content_based.weights.h5'")
    else:
        print("\n--- ❌ Training Failed ---")
