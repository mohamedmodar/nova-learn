from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

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
        name=student.name,
        hashed_password=hashed_password,
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

def get_courses_by_ids(db: Session, course_ids: list[str]):
    # This assumes course_ids are for external courses for now
    return db.query(models.ExternalCourse).filter(models.ExternalCourse.item_id.in_(course_ids)).all()

def create_student_course_interaction(db: Session, student_id: int, interaction: schemas.StudentCourseInteractionCreate):
    db_interaction = models.StudentCourseInteraction(
        **interaction.dict(),
        student_id=student_id
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction 