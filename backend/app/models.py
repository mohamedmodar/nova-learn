import enum
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    Float,
    Text,
    ForeignKey,
    Table,
    Enum,
    DateTime,
    JSON,
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import settings
import datetime

Base = declarative_base()



class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)

    profile = relationship("StudentProfile", back_populates="student", uselist=False)
    interactions = relationship("StudentCourseInteraction", back_populates="student")
    internal_course_progress = relationship(
        "StudentInternalCourseProgress", back_populates="student"
    )
    recommendations = relationship("RecommendationLog", back_populates="student")


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True, nullable=False)
    learning_foundation_confidence = Column(Boolean)
    course_type_preference = Column(String)
    english_proficiency = Column(Integer)
    math_proficiency = Column(Integer)
    technical_skills = Column(JSON)
    programming_concepts_understood = Column(Boolean)
    prior_courses = Column(Text)
    learning_format_preference = Column(String)
    weekly_time_commitment = Column(Integer)
    learning_goals = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="profile")


class ExternalCourse(Base):
    __tablename__ = "external_courses"
    item_id = Column(String, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    level = Column(String)
    duration = Column(Integer)
    rating = Column(Float)
    num_reviews = Column(Integer)
    adjusted_rating = Column(Float)
    skills = Column(JSON)
    url = Column(String)
    provider = Column(String)


class InternalCourse(Base):
    __tablename__ = "internal_courses"
    id = Column(Integer, primary_key=True, index=True)
    playlist_title = Column(String)
    playlist_url = Column(String)
    video_title = Column(String)
    video_url = Column(String)
    channel_url = Column(String)

    progress = relationship(
        "StudentInternalCourseProgress", back_populates="internal_course"
    )


class StudentCourseInteraction(Base):
    __tablename__ = "student_course_interactions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_type = Column(String)  # "external" or "internal"
    course_id = Column(Integer, nullable=False)
    interaction_type = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="interactions")


class StudentInternalCourseProgress(Base):
    __tablename__ = "student_internal_course_progress"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    internal_course_id = Column(
        Integer, ForeignKey("internal_courses.id"), nullable=False
    )
    last_video_index = Column(Integer)
    last_accessed = Column(DateTime, default=datetime.datetime.utcnow)
    completed = Column(Boolean, default=False)

    student = relationship("Student", back_populates="internal_course_progress")
    internal_course = relationship("InternalCourse", back_populates="progress")


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    recommended_courses = Column(JSON)
    recommendation_type = Column(String)
    scores = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="recommendations")


# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 