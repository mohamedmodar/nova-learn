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

def update_student(db: Session, student: models.Student, student_update: schemas.StudentUpdate):
    """Updates a student's information."""
    student.full_name = student_update.full_name
    student.email = student_update.email
    db.commit()
    db.refresh(student)
    return student

def create_student_profile(db: Session, student_id: int, profile: schemas.StudentProfileCreate):
    db_profile = models.StudentProfile(
        student_id=student_id,
        **profile.dict()
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_student_profile(db: Session, student: models.Student, profile_update: schemas.StudentProfileCreate):
    """Updates an existing student profile."""
    if not student.profile:
        return None # Or raise an exception, depending on desired behavior
    
    profile_data = profile_update.dict()
    for key, value in profile_data.items():
        setattr(student.profile, key, value)
        
    db.commit()
    db.refresh(student.profile)
    return student.profile

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

def get_internal_courses_by_playlist(db: Session, playlist_title: str):
    """
    Retrieves all internal course videos for a given playlist title.
    """
    return db.query(models.InternalCourse).filter(models.InternalCourse.playlist_title == playlist_title).all()

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
# Progress CRUD Functions
# =================================

def get_video_progress_for_student(db: Session, student_id: int, video_id: int):
    """Retrieves a specific video progress record for a student."""
    return db.query(models.StudentVideoProgress).filter(
        models.StudentVideoProgress.student_id == student_id,
        models.StudentVideoProgress.video_id == video_id
    ).first()

def get_all_video_progress_for_student(db: Session, student_id: int):
    """Retrieves all video progress records for a student."""
    return db.query(models.StudentVideoProgress).filter(
        models.StudentVideoProgress.student_id == student_id
    ).all()

def create_or_update_video_progress(db: Session, student_id: int, video_id: int, completed: bool):
    """Creates or updates a video progress record for a student."""
    db_progress = get_video_progress_for_student(db, student_id, video_id)
    
    if db_progress:
        db_progress.completed = completed
    else:
        db_progress = models.StudentVideoProgress(
            student_id=student_id,
            video_id=video_id,
            completed=completed
        )
        db.add(db_progress)
    
    db.commit()
    db.refresh(db_progress)
    return db_progress

def get_student_playlist_progress(db: Session, student_id: int):
    """
    Calculates and returns the progress for all playlists a student has interacted with.
    """
    # Step 1: Get all video progress records for the student
    all_progress = db.query(models.StudentVideoProgress).filter(
        models.StudentVideoProgress.student_id == student_id
    ).all()

    if not all_progress:
        return []

    # Step 2: Get the unique IDs of all videos the student has ever interacted with
    interacted_video_ids = list(set([p.video_id for p in all_progress]))
    
    # Step 3: Get the full course objects for these videos
    interacted_courses = db.query(models.InternalCourse).filter(
        models.InternalCourse.id.in_(interacted_video_ids)
    ).all()

    # Step 4: Get the unique playlist titles from these courses
    playlist_titles = list(set([c.playlist_title for c in interacted_courses]))
    
    # Step 5: Get all videos for those playlists to calculate totals
    all_playlist_videos = db.query(models.InternalCourse).filter(
        models.InternalCourse.playlist_title.in_(playlist_titles)
    ).all()

    # Step 6: Organize all videos by playlist
    videos_by_playlist = {}
    for video in all_playlist_videos:
        if video.playlist_title not in videos_by_playlist:
            videos_by_playlist[video.playlist_title] = {
                "videos": [],
                "playlist_url": video.playlist_url
            }
        videos_by_playlist[video.playlist_title]["videos"].append(video.id)

    # Step 7: Calculate progress for each playlist
    completed_videos_map = {p.video_id for p in all_progress if p.completed}
    
    result = []
    for title, data in videos_by_playlist.items():
        total_vids = len(data["videos"])
        completed_vids = len([vid for vid in data["videos"] if vid in completed_videos_map])
        
        result.append(schemas.PlaylistProgress(
            playlist_title=title,
            completed_videos=completed_vids,
            total_videos=total_vids,
            playlist_url=data["playlist_url"]
        ))
        
    return result

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