# generate_fake_interactions.py
"""Generates a synthetic dataset of user-item interactions."""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to sys.path to allow importing recommender_system modules
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PARENT_DIR)

# Now import from the package
import config, utils

# Ensure the data directory exists
os.makedirs(config.DATA_DIR, exist_ok=True)

# Define output path
FAKE_INTERACTIONS_OUTPUT_PATH = os.path.join(config.DATA_DIR, "fake_user_interactions.csv")

# --- Configuration for Fake Data Generation ---
NUM_FAKE_USERS = 500
NUM_INTERACTIONS = 10000 # Total number of interaction events
# Simulate interactions over the last year
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=365)

def generate_fake_interactions():
    """Loads course data and generates fake user-item interactions."""
    print("Starting fake interaction data generation...")

    # 1. Load course data to get valid course IDs
    print(f"Loading course data from: {config.COURSE_DATA_PATH}")
    courses_df = utils.load_course_data(config.COURSE_DATA_PATH)
    if courses_df is None or courses_df.empty:
        print("Failed to load course data. Aborting interaction generation.")
        return
    
    # Use the DataFrame index as the course IDs
    valid_course_ids = courses_df.index.tolist()
    if not valid_course_ids:
        print("No valid course IDs found in course data. Aborting.")
        return
    print(f"Found {len(valid_course_ids)} valid course IDs.")

    # 2. Generate User IDs
    user_ids = [f"user_{i}" for i in range(NUM_FAKE_USERS)]
    print(f"Generated {len(user_ids)} fake user IDs.")

    # 3. Generate Interactions
    print(f"Generating {NUM_INTERACTIONS} interaction events...")
    interaction_data = {
        "user_id": np.random.choice(user_ids, NUM_INTERACTIONS),
        "course_id": np.random.choice(valid_course_ids, NUM_INTERACTIONS),
        # Generate random timestamps within the defined date range
        "timestamp": [START_DATE + timedelta(seconds=np.random.randint(0, int((END_DATE - START_DATE).total_seconds()))) for _ in range(NUM_INTERACTIONS)]
    }
    interactions_df = pd.DataFrame(interaction_data)
    
    # Optional: Add some structure/bias (e.g., popular items, active users)
    # For simplicity, we keep it random for now.
    
    # Ensure correct data types
    interactions_df["course_id"] = interactions_df["course_id"].astype(int) # Assuming index is int
    interactions_df["timestamp"] = pd.to_datetime(interactions_df["timestamp"])
    
    # Sort by timestamp (often useful for sequence-aware models)
    interactions_df = interactions_df.sort_values(by="timestamp").reset_index(drop=True)
    
    print(f"Generated DataFrame shape: {interactions_df.shape}")
    print(interactions_df.head())

    # 4. Save the interactions DataFrame
    print(f"Saving fake interactions to: {FAKE_INTERACTIONS_OUTPUT_PATH}")
    interactions_df.to_csv(FAKE_INTERACTIONS_OUTPUT_PATH, index=False)
    print("Fake interactions saved.")

    # Update config path (in memory for this run)
    print("Updating config path for interaction data...")
    config.INTERACTION_DATA_PATH = FAKE_INTERACTIONS_OUTPUT_PATH
    print(f"Config in memory updated: Interaction Data={config.INTERACTION_DATA_PATH}")

    print("Fake interaction data generation complete.")

if __name__ == "__main__":
    generate_fake_interactions()

