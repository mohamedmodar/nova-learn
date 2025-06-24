import os
import sys
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

# Get the absolute path to the project's root directory
# This assumes the script is in 'backend/scripts/'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(project_root, 'backend'))

# Load environment variables from the .env file in the `backend` directory
dotenv_path = os.path.join(project_root, 'backend', '.env')
load_dotenv(dotenv_path=dotenv_path)

from app.database import SessionLocal
from app.models import InternalCourse, ExternalCourse

def seed_internal_courses(db: Session):
    """Seeds internal courses from the CSV file."""
    print("Seeding internal courses...")
    internal_courses_path = os.path.join(project_root, 'model', 'data', 'final_combined_youtube_data.csv')
    try:
        df = pd.read_csv(internal_courses_path)
        
        for _, row in df.iterrows():
            course = InternalCourse(
                playlist_title=row.get('playlist_title'),
                playlist_url=row.get('playlist_url'),
                video_title=row.get('video_title'),
                video_url=row.get('video_url'),
                channel_url=row.get('channel_url')
            )
            db.add(course)
        
        db.commit()
        print(f"Successfully seeded {len(df)} internal courses.")
    except FileNotFoundError:
        print(f"Error: Could not find internal courses file at {internal_courses_path}")
    except Exception as e:
        db.rollback()
        print(f"An error occurred while seeding internal courses: {e}")

def seed_external_courses(db: Session):
    """Seeds external courses from the CSV file."""
    print("\nSeeding external courses...")
    external_courses_path = os.path.join(project_root, 'model', 'data', 'final(final).csv')
    try:
        df = pd.read_csv(external_courses_path)

        # Rename columns to match the model attributes
        df.rename(columns={
            'item_id': 'item_id',
            'title': 'title',
            'description': 'description',
            'level': 'level',
            'duration_in_seconds': 'duration',
            'rating': 'rating',
            'reviews': 'num_reviews',
            'skills': 'skills',
            'url': 'url',
            'provider': 'provider',
            'adjusted_rating': 'adjusted_rating'
        }, inplace=True)

        successful_seeds = 0
        for index, row in df.iterrows():
            try:
                # Clean up skills data: NaN is not valid JSON. Replace with None (null in DB).
                skills_data = row.get('skills')
                if pd.isna(skills_data):
                    skills_data = None

                # Create the course object safely
                course_data = {
                    "item_id": str(row.get('item_id')), # Ensure item_id is treated as a string
                    "title": row.get('title'),
                    "description": row.get('description'),
                    "level": row.get('level'),
                    "duration": int(row['duration']) if pd.notna(row.get('duration')) else None,
                    "rating": float(row['rating']) if pd.notna(row.get('rating')) else None,
                    "num_reviews": int(row['num_reviews']) if pd.notna(row.get('num_reviews')) else None,
                    "skills": skills_data, # Use the cleaned skills data
                    "url": row.get('url'),
                    "provider": row.get('provider'),
                    "adjusted_rating": float(row.get('adjusted_rating')) if pd.notna(row.get('adjusted_rating')) else None,
                }
                course = ExternalCourse(**course_data)
                db.add(course)
                successful_seeds += 1
            except (ValueError, TypeError) as e:
                # This will catch errors if, for example, 'duration' is not a valid number
                print(f"  - Skipping row {index + 2} due to data conversion error: {e}")
                continue

        db.commit()
        print(f"Successfully seeded {successful_seeds} of {len(df)} external courses.")
    except FileNotFoundError:
        print(f"Error: Could not find external courses file at {external_courses_path}")
    except Exception as e:
        db.rollback()
        print(f"An error occurred during the seeding transaction: {e}")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Clear existing data to avoid duplicates
        print("Clearing existing course data...")
        db.query(InternalCourse).delete()
        db.query(ExternalCourse).delete()
        db.commit()

        seed_internal_courses(db)
        seed_external_courses(db)
    finally:
        db.close()
        print("\nSeeding complete. Database connection closed.")
