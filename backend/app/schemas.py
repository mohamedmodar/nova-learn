from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import datetime

# ====================
# Skill Schemas
# ====================
class SkillBase(BaseModel):
    name: str

class SkillCreate(SkillBase):
    pass

class Skill(SkillBase):
    id: int

    class Config:
        orm_mode = True

# ====================
# Course Schemas
# ====================
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    provider: Optional[str] = None
    level: Optional[str] = None
    duration: Optional[str] = None
    is_external: bool = False
    category: Optional[str] = None
    course_url: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    rating: Optional[float] = None
    enrolled_count: int = 0
    skills: List[Skill] = []

    class Config:
        orm_mode = True

# ====================
# User Schemas
# ====================
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    is_student: Optional[bool] = True

class UserUpdate(UserBase):
    full_name: Optional[str] = None
    is_student: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    has_completed_onboarding: bool

    class Config:
        orm_mode = True

# ====================
# User Preference Schemas
# ====================
class UserPreferenceBase(BaseModel):
    learning_confidence: int
    english_proficiency: int
    math_proficiency: int
    course_preference: str

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreference(UserPreferenceBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

# ====================
# Enrollment Schemas
# ====================
class EnrollmentBase(BaseModel):
    course_id: int

class EnrollmentCreate(EnrollmentBase):
    pass

class EnrollmentUpdate(BaseModel):
    progress: Optional[int] = None
    status: Optional[str] = None

class Enrollment(EnrollmentBase):
    id: int
    user_id: int
    progress: int
    status: str
    enrollment_date: datetime
    course: Course # Include course details in enrollment response

    class Config:
        orm_mode = True

# ====================
# Token Schemas
# ====================
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ====================
# Student Schemas
# ====================
class StudentBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class StudentCreate(StudentBase):
    password: str

class Student(StudentBase):
    id: int
    registration_date: datetime

    class Config:
        from_attributes = True

# ====================
# Student Profile Schemas
# ====================
class StudentProfileBase(BaseModel):
    learning_foundation_confidence: Optional[bool] = None
    course_type_preference: Optional[str] = None
    english_proficiency: Optional[int] = None
    math_proficiency: Optional[int] = None
    technical_skills: Optional[Any] = None
    programming_concepts_understood: Optional[bool] = None
    prior_courses: Optional[str] = None
    learning_format_preference: Optional[str] = None
    weekly_time_commitment: Optional[int] = None
    learning_goals: Optional[str] = None

class StudentProfileCreate(StudentProfileBase):
    pass

class StudentProfileUpdate(StudentProfileBase):
    pass

class StudentProfile(StudentProfileBase):
    id: int
    student_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# ====================
# External Course Schemas
# ====================
class ExternalCourseBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None
    duration: Optional[int] = None
    rating: Optional[float] = None
    num_reviews: Optional[int] = None
    adjusted_rating: Optional[float] = None
    skills: Optional[Any] = None
    url: Optional[str] = None
    provider: Optional[str] = None

class ExternalCourseCreate(ExternalCourseBase):
    pass

class ExternalCourse(ExternalCourseBase):
    item_id: str

    class Config:
        from_attributes = True

# ====================
# Internal Course Schemas
# ====================
class InternalCourseBase(BaseModel):
    playlist_title: Optional[str] = None
    playlist_url: Optional[str] = None
    video_title: Optional[str] = None
    video_url: Optional[str] = None
    channel_url: Optional[str] = None

class InternalCourseCreate(InternalCourseBase):
    pass

class InternalCourse(InternalCourseBase):
    id: int

    class Config:
        from_attributes = True

# ====================
# Interaction Schemas
# ====================
class StudentCourseInteractionBase(BaseModel):
    course_type: str
    course_id: int
    interaction_type: str
    value: Optional[float] = None

class StudentCourseInteractionCreate(StudentCourseInteractionBase):
    pass

class StudentCourseInteraction(StudentCourseInteractionBase):
    id: int
    student_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# ====================
# Progress Schemas
# ====================
class StudentInternalCourseProgressBase(BaseModel):
    internal_course_id: int
    last_video_index: Optional[int] = None
    completed: Optional[bool] = False

class StudentInternalCourseProgressCreate(StudentInternalCourseProgressBase):
    pass

class StudentInternalCourseProgressUpdate(BaseModel):
    last_video_index: Optional[int] = None
    completed: Optional[bool] = None

class StudentInternalCourseProgress(StudentInternalCourseProgressBase):
    id: int
    student_id: int
    last_accessed: datetime

    class Config:
        from_attributes = True

# ====================
# Recommendation Schemas
# ====================
class RecommendationLogBase(BaseModel):
    recommended_courses: Any
    recommendation_type: str
    scores: Optional[Any] = None

class RecommendationLogCreate(RecommendationLogBase):
    pass

class RecommendationLog(RecommendationLogBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True 