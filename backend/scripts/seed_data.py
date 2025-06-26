import os
import sys
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import re
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

# Get the absolute path to the project's root directory
# This assumes the script is in 'backend/scripts/'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(project_root, 'backend'))

# Load environment variables from the .env file in the `backend` directory
dotenv_path = os.path.join(project_root, 'backend', '.env')
load_dotenv(dotenv_path=dotenv_path)

from app.database import SessionLocal, engine
from app.models import Base, ExternalCourse, InternalCourse, Student, StudentProfile, Enrollment
from app.security import get_password_hash

# Define the path to the original CSV file
SOURCE_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'model', 'data', 'final(final).csv')
INTERNAL_COURSES_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'model', 'data', 'coursera_courses_cleaned.csv')

def sanitize_id(item_id):
    """
    Removes problematic characters from an ID to make it database-safe.
    This removes any character that is not a letter, number, hyphen, or underscore.
    """
    if not isinstance(item_id, str):
        return item_id
    return re.sub(r'[^a-zA-Z0-9_-]', '', item_id)

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
    try:
        if not os.path.exists(SOURCE_CSV_PATH):
            print(f"Error: Source data file not found at {SOURCE_CSV_PATH}")
            return

        df = pd.read_csv(SOURCE_CSV_PATH)
        
        # --- Automatic Data Cleaning ---
        if 'item_id' in df.columns:
            print("Sanitizing course IDs for database seeding...")
            df['item_id'] = df['item_id'].apply(sanitize_id)
            print("Sanitizing complete.")
        # -----------------------------
        
        # Ensure 'item_id' is treated as a string
        df['item_id'] = df['item_id'].astype(str)
        
        # Select and rename columns to match the ExternalCourse model
        df_for_db = df[['item_id', 'title', 'description', 'level', 'duration', 'rating', 'num_reviews', 'adjusted_rating', 'skills', 'url', 'provider']].copy()

        print(f"Seeding {len(df_for_db)} external courses...")

        # Convert DataFrame to list of dictionaries and insert
        successful_seeds = 0
        for index, row in df_for_db.iterrows():
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
        print(f"Successfully seeded {successful_seeds} of {len(df_for_db)} external courses.")
    except FileNotFoundError:
        print(f"Error: Could not find external courses file at {SOURCE_CSV_PATH}")
    except Exception as e:
        db.rollback()
        print(f"An error occurred during the seeding transaction: {e}")

def seed_students(db: Session):
    """Seeds a few sample students."""
    print("\nSeeding sample students...")
    students_to_create = [
        {"email": "test.student1@example.com", "password": "password123", "full_name": "Alex Smith"},
        {"email": "test.student2@example.com", "password": "password456", "full_name": "Taylor Jones"},
    ]
    
    created_students = []
    for student_data in students_to_create:
        try:
            hashed_password = get_password_hash(student_data["password"])
            db_student = Student(
                email=student_data["email"], 
                hashed_password=hashed_password,
                full_name=student_data["full_name"]
            )
            db.add(db_student)
            db.commit()
            db.refresh(db_student)
            created_students.append(db_student)
            print(f"  - Created student: {db_student.email}")
        except IntegrityError:
            db.rollback()
            print(f"  - Student {student_data['email']} already exists. Fetching.")
            existing_student = db.query(Student).filter(Student.email == student_data['email']).first()
            if existing_student:
                created_students.append(existing_student)

    # Also create a profile for the first student
    if created_students:
        alex = created_students[0]
        alex_profile = db.query(StudentProfile).filter(StudentProfile.student_id == alex.id).first()
        if not alex_profile:
            profile = StudentProfile(
                student_id=alex.id,
                learning_goals="Learn data science and web development",
                technical_skills=["Python", "SQL", "React"],
                learning_format_preference="visual"
            )
            db.add(profile)
            db.commit()
            print(f"  - Created profile for {alex.email}")
            
    return created_students

def seed_enrollments(db: Session):
    """Seeds some sample enrollments for the test students."""
    print("\nSeeding sample enrollments...")
    
    # Get the students
    student1 = db.query(Student).filter(Student.email == "test.student1@example.com").first()
    
    if not student1:
        print("Could not find sample students to create enrollments for.")
        return

    # Get a few external courses to enroll them in
    courses_to_enroll = db.query(ExternalCourse).limit(5).all()
    if not courses_to_enroll:
        print("Could not find any external courses to create enrollments for.")
        return

    # Enroll student1 in a couple of courses with some progress
    try:
        if len(courses_to_enroll) > 0:
            enrollment1 = Enrollment(student_id=student1.id, course_id=courses_to_enroll[0].item_id, course_type='external', progress=25, status='in_progress')
            db.add(enrollment1)
        
        if len(courses_to_enroll) > 1:
            enrollment2 = Enrollment(student_id=student1.id, course_id=courses_to_enroll[1].item_id, course_type='external', progress=50, status='in_progress')
            db.add(enrollment2)
            
        db.commit()
        print(f"Successfully created enrollments for {student1.email}.")
    except Exception as e:
        db.rollback()
        print(f"An error occurred while seeding enrollments: {e}")

def main():
    """Main function to seed the database."""
    print("Initializing database...")
    
    # Drop tables with CASCADE for PostgreSQL to handle dependencies
    with engine.connect() as connection:
        with connection.begin():
            print("--> Dropping dependent tables with CASCADE...")
            # We drop tables that are known to cause dependency issues first
            connection.execute(text("DROP TABLE IF EXISTS enrollments CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS student_course_interactions CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS students CASCADE"))

    print("--> Dropping all remaining tables...")
    # The standard drop_all might still be useful for other tables
    Base.metadata.drop_all(bind=engine)

    print("--> Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # The seeder no longer needs to clear data, as the tables are fresh
        seed_internal_courses(db)
        seed_external_courses(db)
        seed_students(db)
        seed_enrollments(db)
    finally:
        db.close()
    print("\nDatabase initialization complete.")

if __name__ == "__main__":
    main()
