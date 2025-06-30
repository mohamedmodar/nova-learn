import sys
sys.path.append('app')
from app.database import SessionLocal
from app import models

def cleanup_old_interactions():
    db = SessionLocal()
    
    try:
        # Delete old view interactions that are cluttering the data
        print("Cleaning up old view interactions...")
        
        # Count old view interactions
        old_views = db.query(models.StudentCourseInteraction).filter(
            models.StudentCourseInteraction.interaction_type == 'view'
        ).count()
        
        print(f"Found {old_views} old view interactions to delete")
        
        # Delete them
        deleted_count = db.query(models.StudentCourseInteraction).filter(
            models.StudentCourseInteraction.interaction_type == 'view'
        ).delete()
        
        db.commit()
        print(f"Deleted {deleted_count} old view interactions")
        
        # Check remaining interactions
        remaining = db.query(models.StudentCourseInteraction).count()
        print(f"Remaining interactions: {remaining}")
        
        # Show recent meaningful interactions
        print("\n=== Meaningful interactions remaining ===")
        meaningful = db.query(models.StudentCourseInteraction).filter(
            models.StudentCourseInteraction.interaction_type.in_(['like', 'dislike', 'hover', 'click', 'chat_topic', 'search'])
        ).order_by(models.StudentCourseInteraction.timestamp.desc()).limit(10).all()
        
        for interaction in meaningful:
            print(f"Student {interaction.student_id}: {interaction.interaction_type} - Topic: {interaction.topic} - Value: {interaction.value}")
        
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_old_interactions()