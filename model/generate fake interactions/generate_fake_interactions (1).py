import pandas as pd
import numpy as np
from faker import Faker
import random

def generate_fake_courses(num_courses=50):
    """
    Generates fake course data.
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
    courses_df,
    num_users=20,
    min_interactions=10,
    max_interactions=40,
    out_csv="data/fake_interactions.csv"
):
    """
    Generates a DataFrame of fake user-course interactions using real course data fields.

    Args:
        courses_df (pd.DataFrame): DataFrame with real course data (must have 'title', 'description' and 'adjusted_rating' columns)
        num_users (int): Number of unique fake users to simulate
        min_interactions (int): Minimum interactions per user
        max_interactions (int): Maximum interactions per user
        out_csv (str): Path to save the generated CSV

    Returns:
        pd.DataFrame: DataFrame of fake interactions
    """
    fake = Faker()
    user_ids = [f"user_{i}" for i in range(num_users)]
    
    # Generate random IDs while keeping real titles, descriptions and ratings
    num_courses = len(courses_df)
    item_ids = [f"course_{i}" for i in range(num_courses)]
    titles = courses_df['title'].tolist()
    descriptions = courses_df['description'].tolist()
    ratings = courses_df['adjusted_rating'].tolist()

    interactions = []
    for user_id in user_ids:
        n = random.randint(min_interactions, max_interactions)
        sampled_idx = np.random.choice(len(item_ids), size=n, replace=False)
        for idx in sampled_idx:
            item_id = item_ids[idx]
            title = titles[idx]
            descr = descriptions[idx]
            rating = ratings[idx]
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
                "title": title,
                "description": descr,
                "adjusted_rating": rating,
                "timestamp": fake.date_time_this_year().isoformat()
            })

    df = pd.DataFrame(interactions)
    df.to_csv(out_csv, index=False)
    print(f"Generated {len(df)} fake interactions for {num_users} users.")
    return df

# Example usage:
if __name__ == "__main__":
    # Load your courses data (replace with actual path if needed)
    courses_df = pd.read_csv("data/final(final).csv")
    fake_df = generate_fake_interactions(
        courses_df, 
        num_users=30,
        min_interactions=10,
        max_interactions=50,
        out_csv="fake_interactions.csv"
    )
    print(fake_df.head())