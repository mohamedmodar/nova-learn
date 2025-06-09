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
    An enhanced User Tower using a more powerful architecture to better understand sequences.
    It preprocesses each item in the history before the GRU, and post-processes the result.
    """
    def __init__(self, vector_dim, name="UserTower", **kwargs):
        super().__init__(name=name, **kwargs)
        # 1. Process each course embedding in the sequence independently
        self.preprocess = layers.TimeDistributed(
            layers.Dense(128, activation='relu', name='user_preprocess_dense')
        )
        # 2. GRU layer to understand the sequence context
        self.gru = layers.GRU(128, name='user_gru')
        # 3. Final projection layers to create the final user embedding
        self.postprocess = tf.keras.Sequential([
            layers.BatchNormalization(),
            layers.Dense(128, activation='relu', name='user_postprocess_dense1'),
            layers.Dropout(0.3),
            layers.Dense(SHARED_EMBEDDING_DIM, name='user_postprocess_dense2')
        ])
    
    def call(self, user_history_embeddings, training=False):
        mask = tf.cast(tf.reduce_sum(user_history_embeddings, axis=-1) != 0, tf.bool)
        # Preprocess the sequence
        processed_sequence = self.preprocess(user_history_embeddings, training=training)
        # Get the sequence summary from the GRU
        gru_output = self.gru(processed_sequence, mask=mask, training=training)
        # Postprocess to get final user embedding
        return self.postprocess(gru_output, training=training)

class QueryTower(layers.Layer):
    """A deeper tower to process a single text query embedding with more capacity."""
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
        # Just projects the SBERT query embedding into the shared space
        return self.dense(query_embedding, training=training)

class ItemTower(layers.Layer):
    """A deeper item tower for richer course representations."""
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
        self.user_tower = UserTower(vector_dim)
        self.item_tower = ItemTower(vector_dim)
        self.query_tower = QueryTower() # For text-query based searches
        self.cosine_similarity = layers.Dot(axes=-1, normalize=True)
        
    def call(self, inputs, training=False):
        """
        This call is for inference/prediction.
        It can handle either a user history or a text query embedding.
        """
        user_input, item_candidate_embedding = inputs

        if len(user_input.shape) == 3: # This is a history sequence: (batch, seq_len, embed_dim)
            user_embedding = self.user_tower(user_input, training=training)
        elif len(user_input.shape) == 2: # This is a single query embedding: (batch, embed_dim)
            user_embedding = self.query_tower(user_input, training=training)
        else:
            raise ValueError(f"Unexpected user input shape: {user_input.shape}")

        item_embedding = self.item_tower(item_candidate_embedding, training=training)
        return self.cosine_similarity([user_embedding, item_embedding])

    def train_step(self, data):
        """Custom training step using triplet loss, focused on history."""
        # Unpack the data. Assumes history-based triplets.
        user_history, positive_item, negative_item = data

        with tf.GradientTape() as tape:
            # Get embeddings from the towers
            user_embedding = self.user_tower(user_history, training=True)
            positive_item_embedding = self.item_tower(positive_item, training=True)
            negative_item_embedding = self.item_tower(negative_item, training=True)

            # Calculate triplet loss
            pos_sim = self.cosine_similarity([user_embedding, positive_item_embedding])
            neg_sim = self.cosine_similarity([user_embedding, negative_item_embedding])
            
            margin = 0.1
            loss = tf.reduce_mean(tf.maximum(0., neg_sim - pos_sim + margin))

        # Apply gradients
        gradients = tape.gradient(loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(gradients, self.trainable_variables))

        # Return a dictionary of the metrics to track. The 'loss' key is monitored by the callback.
        return {'loss': loss}
    
    def get_user_embedding(self, user_history_embeddings):
        """Get the user embedding for a given interaction history"""
        # This will now use the powerful GRU-based tower
        return self.user_tower(user_history_embeddings)
    
    def get_item_embedding(self, item_embedding):
        """Get the item embedding for a given course embedding"""
        return self.item_tower(item_embedding)

class CourseRecommender:
    def __init__(self, courses_df, course_sbert_embeddings, model_path=None):
        """
        Initialize the recommender with a trained model and course data.
        
        Args:
            courses_df (pd.DataFrame): DataFrame containing course information.
            course_sbert_embeddings (tf.Tensor): Tensor of SBERT embeddings for the courses.
            model_path (str, optional): Path to the trained model weights.
        """
        # Load SBERT model for encoding queries (if needed for other tasks, though not for recommend())
        self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("SBERT model loaded inside CourseRecommender.")
        
        # --- FIX: Use data passed in constructor, don't load from file ---
        self.courses_df = courses_df
        self.course_embeddings = course_sbert_embeddings
        
        # Get embedding dimension from loaded data
        if self.course_embeddings is not None:
            vector_dim = self.course_embeddings.shape[1]
        else:
            # This case should ideally not be hit if data is passed correctly
            vector_dim = SBERT_EMBEDDING_DIM
            
        # Initialize the model
        self.model = TwoTowerModel(vector_dim)
        
        # Initialize with dummy data to build the model
        dummy_history = tf.zeros((1, MAX_HISTORY_LENGTH, vector_dim))
        dummy_item = tf.zeros((1, vector_dim))
        dummy_query = tf.zeros((1, vector_dim))
        
        # Build history-based path
        _ = self.model((dummy_history, dummy_item))
        # Build query-based path
        _ = self.model((dummy_query, dummy_item))
        
        if self.courses_df is None or self.course_embeddings is None:
            print("Error: CourseRecommender initialized with missing DataFrame or embeddings.")
            self.item_embeddings_norm = None
            return

        # --- FIX: Ensure embedding order matches dataframe order ---
        # The course_id in the dataframe is the string 'item_id', but the model operates on integer indices.
        # The history and recommendations use the DataFrame's integer index.
        # We create a mapping from the STRING item_id to the INTEGER index for robustness, though it may not be used
        # if the history is already provided as integer indices.
        self.course_item_id_to_int_index = {course_id: i for i, course_id in enumerate(self.courses_df['item_id'])}
        # The primary mapping for this class will be from the DataFrame integer index to itself, assuming order is consistent.
        self.course_id_to_index = {i: i for i in self.courses_df.index}

        # Reorder course embeddings to match the dataframe's index. This ensures alignment.
        # This step is critical to prevent misalignment bugs.
        self.ordered_course_embeddings = tf.gather(self.course_embeddings, self.courses_df.index)

        # Load pre-trained weights if provided
        if model_path:
            try:
                self.model.load_weights(model_path)
                print(f"Loaded model weights from {model_path}")
                
                # Pre-compute item embeddings using the correctly ordered tensor
                self.item_embeddings = self.model.get_item_embedding(self.ordered_course_embeddings)
                self.item_embeddings_norm = tf.nn.l2_normalize(self.item_embeddings, axis=-1)
                print("Pre-computed normalized item embeddings in correct order.")
            except Exception as e:
                print(f"Error loading model weights: {e}")
                self.item_embeddings_norm = None
        else:
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
            return recommendations[[col for col in output_columns if col in recommendations.columns]]
            
        except Exception as e:
            print(f"Error generating SBERT recommendations: {e}")
            return pd.DataFrame()
    
    def recommend(self, user_interaction_history, top_k=5):
        """
        Recommend courses based on a user's interaction history.
        
        Args:
            user_interaction_history: A list of STRING item_ids (e.g. 'COURSE-...') the user has interacted with.
            top_k: Number of recommendations to return
            
        Returns:
            DataFrame with top_k recommended courses
        """
        if self.courses_df is None or self.course_embeddings is None or self.item_embeddings_norm is None:
            print("Course data/embeddings not loaded or model weights not specified. Cannot make recommendations.")
            return pd.DataFrame()
        
        if not user_interaction_history:
            print("User history is empty. Cannot make recommendations.")
            # Could fall back to popular items, but for now, returning empty.
            return pd.DataFrame()

        # The history is a list of STRING item_ids. Convert them to integer indices.
        history_indices = [self.course_item_id_to_int_index.get(hist_id) for hist_id in user_interaction_history]
        history_indices = [idx for idx in history_indices if idx is not None]

        if not history_indices:
            print("Could not map any items from history to known course indices.")
            return pd.DataFrame()

        # Get embeddings for the user's history
        history_embeddings = tf.gather(self.course_embeddings, history_indices)
        history_embeddings = tf.expand_dims(history_embeddings, axis=0) # Add batch dimension

        # Pad history to the fixed length the model expects
        history_padded = tf.keras.preprocessing.sequence.pad_sequences(
            history_embeddings.numpy(), maxlen=MAX_HISTORY_LENGTH, padding='post', truncating='post', dtype='float32'
        )
        history_tensor = tf.convert_to_tensor(history_padded)

        # Get user embedding from the model
        user_embedding = self.model.get_user_embedding(history_tensor)
        user_embedding_norm = tf.nn.l2_normalize(user_embedding, axis=-1)
        
        # Compute similarity with all pre-computed item embeddings
        similarity_scores = tf.matmul(user_embedding_norm, self.item_embeddings_norm, transpose_b=True)
        similarity_scores = tf.squeeze(similarity_scores, axis=0)
        
        # --- FIX: Filter out items already in the user's history ---
        # Fetch more recommendations than needed to have backups after filtering.
        k_for_filtering = top_k + len(history_indices)
        top_scores_raw, top_indices_raw = tf.math.top_k(similarity_scores, k=k_for_filtering)
        
        # Create a set of history indices for efficient lookup
        history_set = set(history_indices)
        
        # Loop through the raw recommendations and pick the ones not in the history
        final_indices = []
        final_scores = []
        for score, index in zip(top_scores_raw.numpy(), top_indices_raw.numpy()):
            if index not in history_set:
                final_indices.append(index)
                final_scores.append(score)
            # Stop when we have enough recommendations
            if len(final_indices) == top_k:
                break
        
        if not final_indices:
            print("Warning: All top recommendations were already in the user's history. Returning empty.")
            return pd.DataFrame()

        # The returned indices correspond to the order of `self.item_embeddings`, 
        # which is now aligned with `self.courses_df`.
        recommendations = self.courses_df.iloc[final_indices].copy()
        recommendations['similarity_score'] = final_scores
        
        # Format the output
        return_columns = ['item_id', 'title', 'provider', 'level', 'adjusted_rating', 'similarity_score', 'url']
        if 'skills_list' in recommendations.columns:
            return_columns.insert(4, 'skills_list') # Adjusted index for new column
            
        return recommendations[[col for col in return_columns if col in recommendations.columns]]

def create_interaction_dataset(interactions_path, course_embeddings, batch_size=1024, max_history_length=20):
    """
    Creates a tf.data.Dataset from user interactions for training the Two-Tower model.
    Reads a CSV of interactions, processes them into sequences, and yields triplets
    of (user_history, positive_item, negative_item) for training.
    """
    try:
        interactions_df = pd.read_csv(interactions_path)
        # Assuming columns are user_id, course_id, and maybe interaction_type/timestamp
        print(f"Loaded interactions data from {interactions_path}. Shape: {interactions_df.shape}")
    except FileNotFoundError:
        print(f"Error: Interaction data file not found at {interactions_path}")
        return None
    
    # --- Data Pipeline Diagnostics ---
    print(f"\n--- Data Pipeline Diagnostics ---")
    print(f"Original rows in interactions file: {len(interactions_df)}")

    # --- FIX: Match interaction item_ids (strings) to course catalog indices (integers) ---
    courses_df = pd.read_csv('data/final(final).csv')
    # Create a mapping from the string ID (e.g., 'COURSE-...') to its integer index
    item_id_to_index_map = {item_id: i for i, item_id in enumerate(courses_df['item_id'])}
    
    # Convert interaction item_ids to integer indices using the map
    interactions_df['item_index'] = interactions_df['item_id'].map(item_id_to_index_map)
    
    nan_count = interactions_df['item_index'].isna().sum()
    if nan_count > 0:
        print(f"WARNING: Found {nan_count} interaction item_ids that don't exist in the course catalog. They will be dropped.")
    
    interactions_df.dropna(subset=['item_index'], inplace=True)
    interactions_df['item_id'] = interactions_df['item_index'].astype('int64')
    print(f"Rows after matching interactions to course catalog: {len(interactions_df)}")

    # Group by user to build their interaction history.
    if 'timestamp' in interactions_df.columns:
        interactions_df = interactions_df.sort_values(by=['user_id', 'timestamp'])
    user_histories = interactions_df.groupby('user_id')['item_id'].apply(list).reset_index()
    
    user_histories['history_len'] = user_histories['item_id'].apply(len)
    valid_user_histories = user_histories[user_histories['history_len'] >= 2]
    print(f"Found {len(user_histories)} unique users. {len(valid_user_histories)} of them have 2 or more interactions.")
    print(f"---------------------------------\n")

    if valid_user_histories.empty:
        print("❌ CRITICAL: No users have sufficient interaction history (>= 2) to create training pairs. Cannot proceed.")
        return None
    
    def generator():
        """A generator function that yields training samples."""
        for _, row in valid_user_histories.iterrows():
            history = row['item_id']
            if len(history) < 2:
                continue
            
            # Use a sliding window over the user's history to create training examples
            for i in range(1, len(history)):
                hist_slice = history[:i]
                positive_item_id = history[i]
                
                # Sample a negative item (an item the user has not interacted with)
                while True:
                    negative_item_id = np.random.randint(0, len(course_embeddings))
                    if negative_item_id not in history:
                        break
                
                # Get embeddings for the history sequence and the items
                history_embeddings = tf.gather(course_embeddings, hist_slice[-max_history_length:])
                positive_item_embedding = tf.gather(course_embeddings, positive_item_id)
                negative_item_embedding = tf.gather(course_embeddings, negative_item_id)
                
                # Pad the history sequence to a fixed length
                history_padded = np.zeros((max_history_length, course_embeddings.shape[1]), dtype=np.float32)
                h_len = min(len(history_embeddings.numpy()), max_history_length)
                history_padded[:h_len] = history_embeddings.numpy()
                
                yield (history_padded, positive_item_embedding, negative_item_embedding)

    # Create the dataset from the generator
    dataset = tf.data.Dataset.from_generator(
        generator,
        output_signature=(
            tf.TensorSpec(shape=(max_history_length, course_embeddings.shape[1]), dtype=tf.float32),
            tf.TensorSpec(shape=(course_embeddings.shape[1],), dtype=tf.float32),
            tf.TensorSpec(shape=(course_embeddings.shape[1],), dtype=tf.float32)
        )
    )
    
    return dataset.shuffle(10000).batch(batch_size).prefetch(tf.data.AUTOTUNE)

def train_two_tower_model(model, course_embeddings, epochs=10, batch_size=1024, save_path='two_tower_real_interactions.weights.h5'):
    """
    Train the two-tower model using real interaction data from a CSV file.
    """
    # Create the training dataset from user interactions
    interactions_path = 'data/fake_interactions.csv'
    dataset = create_interaction_dataset(interactions_path, course_embeddings, batch_size, MAX_HISTORY_LENGTH)
    
    if dataset is None:
        print("Could not create dataset. Aborting training.")
        return None

    # Since training data only uses the UserTower, freeze the QueryTower to avoid gradient errors.
    model.query_tower.trainable = False

    # Compile the model with an optimizer. The loss is handled in the custom train_step.
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), 
        loss="mse", # Loss here is a placeholder metric
        run_eagerly=True # Run eagerly for better debugging as suggested by the error
    )
    
    # Checkpoint to save the best model weights during training
    checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        save_path,
        monitor='loss',
        save_best_only=True,
        save_weights_only=True,
        verbose=1
    )
    
    # Train the model
    print("Starting training of Two-Tower model on real user interactions...")
    history = model.fit(
        dataset,
        epochs=epochs,
        callbacks=[checkpoint_callback]
    )
    
    print("Training finished.")
    # Unfreeze the query tower in case the model is used for inference later in the same session
    model.query_tower.trainable = True
    return history

if __name__ == "__main__":
    print("--- Running Two-Tower Model Training Script ---")
    
    # 1. Load course embeddings (needed for the dataset generator and model instantiation)
    try:
        with open('models/course_sbert_embeddings.pkl', 'rb') as f:
            course_embeddings = pickle.load(f)
        
        course_embeddings_tensor = tf.convert_to_tensor(course_embeddings, dtype=tf.float32)
        print(f"✅ Loaded course embeddings. Shape: {course_embeddings_tensor.shape}")
        embedding_dim = course_embeddings_tensor.shape[1]
    except FileNotFoundError:
        print("❌ Error: Course SBERT embeddings not found at 'models/course_sbert_embeddings.pkl'.")
        print("Please run the SBERT embedding generation script first.")
        exit()
    except Exception as e:
        print(f"❌ An error occurred loading embeddings: {e}")
        exit()

    # 2. Instantiate the Two-Tower Model
    print("\nInstantiating the Two-Tower Model...")
    two_tower_model = TwoTowerModel(vector_dim=embedding_dim)
    
    # Dummy call to build the model's layers before training
    dummy_history = tf.zeros((1, MAX_HISTORY_LENGTH, embedding_dim))
    dummy_item = tf.zeros((1, embedding_dim))
    dummy_query = tf.zeros((1, embedding_dim))
    _ = two_tower_model((dummy_history, dummy_item)) # Build history path
    _ = two_tower_model((dummy_query, dummy_item))   # Build query path
    print("✅ Model instantiated successfully.")
    
    # 3. Start the training process
    print("\nStarting the training process...")
    training_history = train_two_tower_model(
        two_tower_model, 
        course_embeddings_tensor, 
        epochs=10,  # You can adjust this
        batch_size=512 # Adjust based on your system's memory
    )
    
    if training_history:
        print("\n--- ✅ Training Complete ---")
        print("Model weights have been saved to 'two_tower_real_interactions.weights.h5'")
    else:
        print("\n--- ❌ Training Failed ---")
