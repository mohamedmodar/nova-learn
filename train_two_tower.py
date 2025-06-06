import tensorflow as tf
import numpy as np
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer
from adapted_two_tower_model import TwoTowerModel, generate_training_pairs

# Constants
SBERT_EMBEDDING_DIM = 384
SHARED_EMBEDDING_DIM = 64
BATCH_SIZE = 1024
EPOCHS = 10
STEPS_PER_EPOCH = 100

def load_data():
    """Load course data and SBERT embeddings"""
    print("Loading course data...")
    df_courses = pd.read_csv('data/final(final).csv')
    print(f"Loaded {len(df_courses)} courses")
    
    print("\nLoading SBERT embeddings...")
    with open('models/course_sbert_embeddings.pkl', 'rb') as f:
        course_embeddings = pickle.load(f)
    course_embeddings = tf.convert_to_tensor(course_embeddings, dtype=tf.float32)
    print(f"Loaded embeddings with shape: {course_embeddings.shape}")
    
    return df_courses, course_embeddings

def create_training_dataset(course_embeddings):
    """Create a TensorFlow dataset for training"""
    dataset = tf.data.Dataset.from_generator(
        lambda: generate_training_pairs(course_embeddings, BATCH_SIZE, STEPS_PER_EPOCH * EPOCHS),
        output_signature=(
            (
                tf.TensorSpec(shape=(None, course_embeddings.shape[1]), dtype=tf.float32),
                tf.TensorSpec(shape=(None, course_embeddings.shape[1]), dtype=tf.float32),
                tf.TensorSpec(shape=(None, course_embeddings.shape[1]), dtype=tf.float32)
            ),
            tf.TensorSpec(shape=(None, 1), dtype=tf.float32)
        )
    )
    return dataset.prefetch(tf.data.AUTOTUNE)

def main():
    # Load data
    df_courses, course_embeddings = load_data()
    
    # Initialize model
    print("\nInitializing Two-Tower model...")
    model = TwoTowerModel(course_embeddings.shape[1])
    
    # Create training dataset
    print("\nCreating training dataset...")
    train_dataset = create_training_dataset(course_embeddings)
    
    # Compile model
    print("\nCompiling model...")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='mse',
        metrics=['mae']
    )
    
    # Set up callbacks
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            'two_tower.weights.h5',
            monitor='loss',
            save_best_only=True,
            save_weights_only=True,
            verbose=1
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor='loss',
            patience=3,
            restore_best_weights=True
        )
    ]
    
    # Train model
    print("\nStarting training...")
    history = model.fit(
        train_dataset,
        epochs=EPOCHS,
        steps_per_epoch=STEPS_PER_EPOCH,
        callbacks=callbacks,
        verbose=1
    )
    
    print("\nTraining completed!")
    print("Model weights saved to 'two_tower.weights.h5'")
    
    # Save training history
    with open('training_history.pkl', 'wb') as f:
        pickle.dump(history.history, f)
    print("Training history saved to 'training_history.pkl'")

if __name__ == "__main__":
    main() 