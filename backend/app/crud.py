from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext
from fastapi import HTTPException, status
from typing import List
import ast

def _parse_skills(skills_str: str) -> List[str]:
    """Safely parses a string representation of a list into a list of strings."""
    if not skills_str or not isinstance(skills_str, str):
        return []
    try:
        # ast.literal_eval is a safe way to evaluate a string containing a Python literal
        skills_list = ast.literal_eval(skills_str)
        if isinstance(skills_list, list):
            return [str(item) for item in skills_list]
        return []
    except (ValueError, SyntaxError):
        # Handle cases where the string is not a valid literal (e.g., "skill1, skill2")
        return [s.strip() for s in skills_str.split(',') if s.strip()]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ====================
# User CRUD
# ====================
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_student=user.is_student,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ====================
# Student CRUD
# ====================
def get_student(db: Session, student_id: int):
    return db.query(models.Student).filter(models.Student.id == student_id).first()

def get_student_by_email(db: Session, email: str):
    return db.query(models.Student).filter(models.Student.email == email).first()

def get_students(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Student).offset(skip).limit(limit).all()

def create_student(db: Session, student: schemas.StudentCreate):
    hashed_password = pwd_context.hash(student.password)
    db_student = models.Student(
        email=student.email,
        hashed_password=hashed_password,
        full_name=student.full_name
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def create_student_profile(db: Session, student_id: int, profile: schemas.StudentProfileCreate):
    db_profile = models.StudentProfile(
        student_id=student_id,
        **profile.dict()
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

# ====================
# Course CRUD
# ====================
def get_courses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Course).offset(skip).limit(limit).all()

def create_course(db: Session, course: schemas.CourseCreate):
    db_course = models.Course(**course.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

def get_internal_courses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.InternalCourse).offset(skip).limit(limit).all()

def get_external_course_by_id(db: Session, course_id: str):
    return db.query(models.ExternalCourse).filter(models.ExternalCourse.item_id == course_id).first()

def get_internal_course_by_id(db: Session, course_id: int):
    return db.query(models.InternalCourse).filter(models.InternalCourse.id == course_id).first()

def get_external_courses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ExternalCourse).offset(skip).limit(limit).all()

def get_student_interactions(db: Session, student_id: int):
    return db.query(models.StudentCourseInteraction).filter(models.StudentCourseInteraction.student_id == student_id).all()

def get_course_by_id(db: Session, course_id: str):
    """
    Retrieves a course by its ID from either internal or external courses.
    Returns the course object and its type ('internal' or 'external').
    """
    # Try to get as external course first (since IDs are strings)
    course = db.query(models.ExternalCourse).filter(models.ExternalCourse.item_id == str(course_id)).first()
    if course:
        return course, "external"

    # If not found, try to find in internal courses (ID is integer)
    try:
        internal_course_id = int(course_id)
        course = db.query(models.InternalCourse).filter(models.InternalCourse.id == internal_course_id).first()
        if course:
            return course, "internal"
    except (ValueError, TypeError):
        # course_id is not a valid integer, so it can't be an internal course
        pass

    return None, None

def get_courses_by_ids(db: Session, course_ids: list[str]):
    # This assumes course_ids are for external courses for now
    return db.query(models.ExternalCourse).filter(models.ExternalCourse.item_id.in_(course_ids)).all()

def create_student_course_interaction(db: Session, student_id: int, interaction: schemas.StudentCourseInteractionCreate):
    """
    Creates a new interaction record for a student.
    - If course_id is provided, it's a course interaction.
    - If topic is provided, it's a topic interaction.
    """
    course_type = None
    if interaction.course_id:
        course, c_type = get_course_by_id(db, interaction.course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID '{interaction.course_id}' not found."
            )
        course_type = c_type

    db_interaction = models.StudentCourseInteraction(
        student_id=student_id,
        course_id=str(interaction.course_id) if interaction.course_id else None,
        topic=interaction.topic,
        interaction_type=interaction.interaction_type,
        value=interaction.value,
        course_type=course_type
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

# =================================
# Enrollment CRUD Functions
# =================================

def create_enrollment(db: Session, student_id: int, course_id: str, course_type: str):
    """Creates a new course enrollment for a student."""
    db_enrollment = models.Enrollment(
        student_id=student_id,
        course_id=str(course_id),
        course_type=course_type
    )
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment

def get_enrollment_by_course_and_student(db: Session, student_id: int, course_id: str):
    """Retrieves a specific enrollment for a student and course."""
    return db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student_id,
        models.Enrollment.course_id == str(course_id)
    ).first()

def get_enrollments_by_student(db: Session, student_id: int):
    """Retrierieves all enrollments for a given student."""
    return db.query(models.Enrollment).filter(models.Enrollment.student_id == student_id).all()

def update_enrollment_progress(db: Session, db_enrollment: models.Enrollment, status: str = None, progress: int = None):
    """Updates the progress or status of an enrollment."""
    if status is not None:
        db_enrollment.status = status
    if progress is not None:
        db_enrollment.progress = progress
    
    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment

# =================================
# Search Functions
# =================================

def search_courses_by_query(db: Session, query: str, course_type: str = "all") -> List[schemas.Course]:
    """
    Performs a case-insensitive search and maps results to the unified Course schema.
    Can filter by course_type: "internal", "external", or "all".
    """
    results = []

    # Search and map External Courses
    if course_type in ["all", "external"]:
        external_courses = db.query(models.ExternalCourse).filter(
            models.ExternalCourse.title.ilike(f"%{query}%")
        ).all()
        for course in external_courses:
            results.append(schemas.Course(
                id=course.item_id,
                title=course.title,
                description=course.description,
                url=course.url,
                provider=course.provider,
                course_type='external',
                skills=_parse_skills(course.skills)
            ))

    # Search and map Internal Courses
    if course_type in ["all", "internal"]:
        internal_courses = db.query(models.InternalCourse).filter(
            models.InternalCourse.playlist_title.ilike(f"%{query}%")
        ).all()
        for course in internal_courses:
            results.append(schemas.Course(
                id=str(course.id),
                title=course.playlist_title,
                description=f"A playlist of YouTube videos on {course.playlist_title}.",
                url=course.playlist_url,
                provider="YouTube",
                course_type='internal',
                skills=[]
            ))
        
    return results 