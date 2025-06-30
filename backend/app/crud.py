from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext
from fastapi import HTTPException, status
from typing import List
import ast
import json
from sqlalchemy import or_
from sqlalchemy.types import Text

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

def extract_topic_from_course(course, course_type: str) -> str:
    """Extract topic/skills from a course to populate the topic field in interactions."""
    if course_type == "external" and course:
        # For external courses, try to extract from skills first, then title
        topics = []
        if hasattr(course, 'skills') and course.skills:
            try:
                # Handle both string and JSON formats
                if isinstance(course.skills, str):
                    skills_data = json.loads(course.skills)
                else:
                    skills_data = course.skills
                
                if isinstance(skills_data, list):
                    topics.extend([str(skill).strip() for skill in skills_data if skill])
                elif isinstance(skills_data, dict):
                    # If skills is a dict, try to get values
                    for value in skills_data.values():
                        if isinstance(value, list):
                            topics.extend([str(skill).strip() for skill in value if skill])
                        elif value:
                            topics.append(str(value).strip())
            except (json.JSONDecodeError, TypeError):
                pass
        
        # If no skills found, extract from title
        if not topics and hasattr(course, 'title') and course.title:
            # Extract key terms from title (basic approach)
            title_words = course.title.lower().split()
            # Filter out common words and keep meaningful terms
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'complete', 'course', 'tutorial', 'guide', 'learn', 'learning'}
            meaningful_words = [word for word in title_words if word not in stop_words and len(word) > 2]
            topics.extend(meaningful_words[:3])  # Take first 3 meaningful words
        
        return " ".join(topics[:5]) if topics else course.title  # Max 5 topics or fallback to title
    
    elif course_type == "internal" and course:
        # For internal courses, extract from playlist and video titles
        topics = []
        if hasattr(course, 'playlist_title') and course.playlist_title:
            playlist_words = course.playlist_title.lower().split()
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'complete', 'course', 'tutorial', 'guide', 'learn', 'learning', 'playlist'}
            meaningful_words = [word for word in playlist_words if word not in stop_words and len(word) > 2]
            topics.extend(meaningful_words[:3])
        
        if hasattr(course, 'video_title') and course.video_title:
            video_words = course.video_title.lower().split()
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'complete', 'course', 'tutorial', 'guide', 'learn', 'learning', 'video'}
            meaningful_words = [word for word in video_words if word not in stop_words and len(word) > 2]
            topics.extend(meaningful_words[:2])
        
        return " ".join(list(set(topics))[:5]) if topics else course.playlist_title or course.video_title
    
    return ""

def get_interaction_value(interaction_type: str, course=None) -> float:
    """Generate appropriate values for different interaction types to help with personalization."""
    if interaction_type == "like":
        return 5.0  # High positive value for likes
    elif interaction_type == "dislike":
        return 1.0  # Low positive value (we track dislikes separately, but still need a value)
    elif interaction_type == "search":
        return 3.0  # Medium value for search interest
    elif interaction_type == "chat_topic":
        return 4.0  # High value for chat topics (shows strong interest)
    elif interaction_type == "hover":
        return 2.5  # Medium value for meaningful hover (3+ seconds)
    elif interaction_type == "click":
        return 3.5  # High value for active clicking
    elif interaction_type == "enroll":
        return 4.5  # Very high value for enrollment
    elif interaction_type == "complete":
        return 5.0  # Highest value for completion
    elif interaction_type == "continue":
        return 4.0  # High value for continuing a course
    else:
        return 2.0  # Default value for unknown interaction types

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
    Now includes automatic topic extraction from courses and proper value assignment.
    """
    course_type = None
    extracted_topic = interaction.topic  # Use provided topic if available
    
    if interaction.course_id:
        course, c_type = get_course_by_id(db, interaction.course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID '{interaction.course_id}' not found."
            )
        course_type = c_type
        
        # Extract topic from course if not provided
        if not extracted_topic:
            extracted_topic = extract_topic_from_course(course, course_type)
    
    # Ensure every interaction has a value
    interaction_value = interaction.value if interaction.value is not None else get_interaction_value(
        interaction.interaction_type, 
        course if interaction.course_id else None
    )

    db_interaction = models.StudentCourseInteraction(
        student_id=student_id,
        course_id=str(interaction.course_id) if interaction.course_id else None,
        topic=extracted_topic,  # Now always populated for course interactions
        interaction_type=interaction.interaction_type,
        value=interaction_value,  # Now always has a meaningful value
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
    Performs a simple case-insensitive search on course titles and descriptions.
    Can filter by course_type: "internal", "external", or "all".
    """
    results = []

    # Search External Courses (title and description only)
    if course_type in ["all", "external"]:
        try:
            external_courses = db.query(models.ExternalCourse).filter(
                or_(
                    models.ExternalCourse.title.ilike(f"%{query}%"),
                    models.ExternalCourse.description.ilike(f"%{query}%")
                )
            ).limit(50).all()  # Limit results to avoid performance issues
            
            for course in external_courses:
                # Parse skills safely
                skills = []
                try:
                    skills = _parse_skills(course.skills)
                except:
                    skills = []
                    
                results.append(schemas.Course(
                    id=course.item_id,
                    title=course.title,
                    description=course.description or "",
                    url=course.url or "",
                    provider=course.provider or "Unknown",
                    course_type='external',
                    skills=skills,
                    rating=course.adjusted_rating if course.adjusted_rating else 0.0,
                    level=course.level or "All Levels",
                    duration=course.duration or 0
                ))
        except Exception as e:
            print(f"Error searching external courses: {e}")

    # Search Internal Courses (playlist titles only)
    if course_type in ["all", "internal"]:
        try:
            internal_courses = db.query(models.InternalCourse).filter(
                models.InternalCourse.playlist_title.ilike(f"%{query}%")
            ).limit(50).all()
            
            # Group by playlist to avoid duplicates
            playlists_seen = set()
            for course in internal_courses:
                if course.playlist_title and course.playlist_title not in playlists_seen:
                    playlists_seen.add(course.playlist_title)
                    results.append(schemas.Course(
                        id=str(course.id),
                        title=course.playlist_title,
                        description=f"A playlist of YouTube videos on {course.playlist_title}.",
                        url=course.playlist_url or "",
                        provider="YouTube",
                        course_type='internal',
                        skills=[]
                    ))
        except Exception as e:
            print(f"Error searching internal courses: {e}")
        
    return results 