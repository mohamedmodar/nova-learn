import sys
sys.path.append('app')
from app.database import SessionLocal
from app import models

def check_interactions():
    db = SessionLocal()
    
    try:
        # Check total number of interactions
        total_interactions = db.query(models.StudentCourseInteraction).count()
        print(f"Total interactions in database: {total_interactions}")
        
        # Check recent interactions
        print("\n=== Recent interactions ===")
        interactions = db.query(models.StudentCourseInteraction).order_by(
            models.StudentCourseInteraction.timestamp.desc()
        ).limit(10).all()
        
        for i in interactions:
            print(f"Student {i.student_id}: {i.interaction_type} - Course: {i.course_id} - Topic: {i.topic} - Value: {i.value}")
        
        # Check like interactions specifically
        print("\n=== Like interactions ===")
        likes = db.query(models.StudentCourseInteraction).filter(
            models.StudentCourseInteraction.interaction_type == 'like'
        ).limit(10).all()
        
        for like in likes:
            print(f"Student {like.student_id}: Course {like.course_id} - Topic: {like.topic} - Value: {like.value}")
        
        # Check Node.js related interactions
        print("\n=== Node.js related interactions ===")
        nodejs_interactions = db.query(models.StudentCourseInteraction).filter(
            models.StudentCourseInteraction.topic.ilike('%node%')
        ).all()
        
        for interaction in nodejs_interactions:
            print(f"Student {interaction.student_id}: {interaction.interaction_type} - Topic: {interaction.topic} - Value: {interaction.value}")
        
        # Check external courses with Node.js in title or skills
        print("\n=== Node.js courses in database ===")
        nodejs_courses = db.query(models.ExternalCourse).filter(
            models.ExternalCourse.title.ilike('%node%')
        ).limit(5).all()
        
        for course in nodejs_courses:
            print(f"Course {course.item_id}: {course.title}")
            print(f"  Skills: {course.skills}")
        
        # Check if there are any students
        print("\n=== Students in database ===")
        students = db.query(models.Student).limit(5).all()
        for student in students:
            print(f"Student {student.id}: {student.full_name} ({student.email})")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_interactions() 