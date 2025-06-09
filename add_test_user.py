import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

# Add parent directory for package import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

import config
import utils

def add_test_user():
    """Add a new test user with specific interactions"""
    print("Loading existing interaction data...")
    try:
        interactions_df = pd.read_csv(config.INTERACTION_DATA_PATH, encoding='utf-8')
    except FileNotFoundError:
        print(f"Error: {config.INTERACTION_DATA_PATH} not found")
        return
        
    # Load course data to get valid course IDs
    print("Loading course data...")
    courses_df = utils.load_course_data(config.COURSE_DATA_PATH)
    if courses_df is None or courses_df.empty:
        print("Failed to load course data")
        return
        
    # Create a new test user
    test_user_id = "test_user_003"
    
    # Define specific interactions
    specific_interactions = [
        {
            'item_id': 'COURSE-250607-010-PW-AF',
            'rating': 5.0
        },
        {
            'item_id': 'COURSE-250607-100-XE-BY',
            'rating': 1.0
        },
        {
            'item_id': 'COURSE-250607-126-HN-BA',
            'rating': 4.0
        }
    ]
    
    # Create new interactions
    new_interactions = []
    for interaction in specific_interactions:
        # Get course info
        course_info = courses_df[courses_df['item_id'] == interaction['item_id']]
        if course_info.empty:
            print(f"Warning: Course {interaction['item_id']} not found in course data")
            continue
            
        course = course_info.iloc[0]
        new_interactions.append({
            'user_id': test_user_id,
            'item_id': interaction['item_id'],
            'interaction_type': 'rating',  # All interactions are ratings
            'value': interaction['rating'],
            'title': course['title'],
            'description': course.get('description', ''),
            'adjusted_rating': course.get('adjusted_rating', 0.0),
            'timestamp': datetime.now().isoformat()
        })
    
    # Create DataFrame for new interactions
    new_interactions_df = pd.DataFrame(new_interactions)
    
    # Combine with existing interactions
    combined_df = pd.concat([interactions_df, new_interactions_df], ignore_index=True)
    
    # Save updated interactions
    print(f"Saving updated interactions with new test user {test_user_id}...")
    combined_df.to_csv(config.INTERACTION_DATA_PATH, index=False)
    print(f"Successfully added test user {test_user_id} with {len(new_interactions)} interactions")
    print("\nTest user interactions:")
    print(new_interactions_df[['item_id', 'interaction_type', 'value']].to_string())

if __name__ == "__main__":
    add_test_user() 