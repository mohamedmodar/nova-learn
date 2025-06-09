import pandas as pd
import numpy as np
from faker import Faker
import random
import os # Import os for path handling
import sys # Import sys for path manipulation
import csv # Import the csv module for quoting options

# --- Add Parent Directory for Package Import ---
# This ensures that 'config' and 'utils' can be imported if this script is in a subdirectory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# Now import from the package
import config # Assuming config.py is in the parent directory
import utils # Assuming utils.py is in the parent directory

def generate_fake_courses(num_courses=50):
    """
    Generates fake course data. (Note: This function is generally not used
    when you're loading real course data from a CSV like final(final).csv).
    """
    fake = Faker()
    courses = []
    
    for i in range(num_courses):
        courses.append({
            'item_id': f'course_{i}',
            'title': fake.catch_phrase(),
            'description': fake.text(max_nb_chars=200),
            'adjusted_rating': round(np.random.uniform(1, 5), 1)
        })
    
    return pd.DataFrame(courses)

def generate_fake_interactions(
    courses_df, # This courses_df will already have the correct item_id format from utils.load_course_data
    num_users=20,
    min_interactions=3,
    max_interactions=100,
    out_csv="fake_interactions.csv"
):
    """
    Generates a DataFrame of fake user-course interactions using *actual* course data fields
    from the provided courses_df, ensuring item_id consistency.

    Args:
        courses_df (pd.DataFrame): DataFrame with real course data (already preprocessed by utils.py).
                                   MUST have 'item_id', 'title', 'description' (or 'description'),
                                   and 'adjusted_rating' columns.
                                   'item_id's should already be in 'COURSE-250607-XXX' format.
        num_users (int): Number of unique fake users to simulate.
        min_interactions (int): Minimum interactions per user.
        max_interactions (int): Maximum interactions per user.
        out_csv (str): Path to save the generated CSV.

    Returns:
        pd.DataFrame: DataFrame of fake interactions.
    """
    fake = Faker()
    user_ids = [f"user_{i}" for i in range(num_users)]
    
    # --- KEY CHANGE: Get item details directly from the provided courses_df ---
    # This ensures consistency of item_ids, titles, descriptions, and ratings.
    if courses_df.empty or 'item_id' not in courses_df.columns:
        print("Error: courses_df is empty or missing 'item_id' column. Cannot generate interactions.")
        return pd.DataFrame()

    # Create a mapping from item_id to its full course details for easy lookup
    item_details_map = courses_df.set_index('item_id').to_dict(orient='index')
    all_item_ids_from_courses_df = courses_df['item_id'].tolist()

    interactions = []
    for user_id in user_ids:
        n = random.randint(min_interactions, max_interactions)
        
        # Ensure we don't try to sample more unique items than available in the actual courses_df
        actual_available_items_count = len(all_item_ids_from_courses_df)
        if n > actual_available_items_count:
            n = actual_available_items_count 
            print(f"Warning: User {user_id} requested {max_interactions} interactions, but only {actual_available_items_count} unique courses available. Capping at {n}.")

        # Sample item IDs directly from the list of valid item IDs
        # use replace=False to ensure unique interactions for a single user in one batch
        sampled_item_ids = np.random.choice(all_item_ids_from_courses_df, size=n, replace=False) 
        
        for item_id in sampled_item_ids:
            course_details = item_details_map.get(item_id, {})
            
            # Use 'description' if it exists, otherwise 'description'
            description_col = 'description' if 'description' in course_details else 'description'

            title = course_details.get('title', 'Unknown Title')
            descr = course_details.get(description_col, 'No Description')
            rating = course_details.get('adjusted_rating', 0.0) # Default to 0.0 if not found

            interaction_type = random.choices(
                ["click", "like", "rating"], weights=[0.6, 0.2, 0.2]
            )[0]
            value = (
                1 if interaction_type in ["click", "like"]
                else round(np.clip(rating + np.random.normal(0, 1), 1, 5), 1)
            )
            interactions.append({
                "user_id": user_id,
                "item_id": item_id,
                "interaction_type": interaction_type,
                "value": value,
                "title": title, # Store actual title from courses_df
                "description": descr, # Store actual description from courses_df
                "adjusted_rating": rating, # Store actual rating from courses_df
                "timestamp": fake.date_time_this_year().isoformat()
            })

    df = pd.DataFrame(interactions)
    # --- FIX: Force quoting of all fields and use UTF-8 encoding ---
    df.to_csv(out_csv, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8') 
    print(f"Generated {len(df)} fake interactions for {num_users} users.")
    return df

# Example usage:
if __name__ == "__main__":
    print("--- Running generate_fake_interactions (2).py ---") # Changed print statement to reflect new name
    # Load your courses data using utils.load_course_data to ensure item_id consistency
    # This is CRITICAL: courses_df_for_faker will have the correct item_id format from utils.py
    courses_df_for_faker = utils.load_course_data(config.COURSE_DATA_PATH)

    if courses_df_for_faker is None or courses_df_for_faker.empty:
        print("Error: Course data could not be loaded for generating fake interactions. Please check config.COURSE_DATA_PATH and utils.load_course_data.")
    else:
        # --- Configure parameters for fake interaction generation ---
        fake_df = generate_fake_interactions(
            courses_df_for_faker, # Pass the preprocessed courses_df
            num_users=4000, # Use a large number of users for effective model training
            min_interactions=3,
            max_interactions=10,
            out_csv=config.INTERACTION_DATA_PATH # Use the path defined in config.py
        )
        print("\nGenerated fake_interactions.csv head:")
        print(fake_df.head())
        print(f"\nTotal interactions generated: {len(fake_df)}")
