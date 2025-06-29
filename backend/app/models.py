import enum
from sqlalchemy import (
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
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)
    has_completed_onboarding = Column(Boolean, default=False, nullable=False)

    enrollments = relationship("Enrollment", back_populates="student")
    profile = relationship("StudentProfile", back_populates="student", uselist=False)
    interactions = relationship("StudentCourseInteraction", back_populates="student")
    recommendations = relationship("RecommendationLog", back_populates="student")
    video_progress = relationship("StudentVideoProgress", back_populates="student")


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

    progress = relationship("StudentVideoProgress", back_populates="video")


class StudentCourseInteraction(Base):
    __tablename__ = "student_course_interactions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # An interaction can be with a course OR about a topic
    course_id = Column(String, nullable=True) 
    course_type = Column(String, nullable=True) # 'external' or 'internal'
    topic = Column(String, index=True, nullable=True) # The learned topic, e.g., from search or chat

    interaction_type = Column(String, nullable=False) # 'like', 'dislike', 'search', 'chat_topic'
    value = Column(Float, nullable=True)  # For ratings, etc.
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
 

    student = relationship("Student", back_populates="interactions")


class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(String, nullable=False)
    course_type = Column(String, nullable=False) # "external" or "internal"
    enrollment_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="in_progress") # e.g., "in_progress", "completed"
    progress = Column(Integer, default=0) # e.g., a percentage from 0 to 100

    student = relationship("Student", back_populates="enrollments")


class StudentVideoProgress(Base):
    __tablename__ = "student_video_progress"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("internal_courses.id"), nullable=False)
    completed = Column(Boolean, default=False, nullable=False)

    student = relationship("Student", back_populates="video_progress")
    video = relationship("InternalCourse", back_populates="progress")


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    recommended_courses = Column(JSON)
    recommendation_type = Column(String)
    scores = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="recommendations") 