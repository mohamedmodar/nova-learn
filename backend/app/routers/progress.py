from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..dependencies import get_db, get_current_student

router = APIRouter(
    prefix="/progress",
    tags=["progress"],
    responses={404: {"description": "Not found"}},
)

@router.get("/videos", response_model=List[schemas.StudentVideoProgress])
def read_student_video_progress(
    db: Session = Depends(get_db),
    current_student: schemas.Student = Depends(get_current_student)
):
    """
    Retrieve all video progress for the currently authenticated student.
    """
    return crud.get_all_video_progress_for_student(db, student_id=current_student.id)

@router.post("/videos", response_model=schemas.StudentVideoProgress)
def update_student_video_progress(
    progress_update: schemas.StudentVideoProgressCreate,
    db: Session = Depends(get_db),
    current_student: schemas.Student = Depends(get_current_student)
):
    """
    Create or update a video progress record for the currently authenticated student.
    This also creates an interaction record.
    """
    # Create or update the progress
    progress = crud.create_or_update_video_progress(
        db, 
        student_id=current_student.id, 
        video_id=progress_update.video_id, 
        completed=progress_update.completed
    )

    # Log the interaction
    interaction_type = "video_complete" if progress_update.completed else "video_uncomplete"
    interaction = schemas.StudentCourseInteractionCreate(
        course_id=str(progress_update.video_id),
        interaction_type=interaction_type
    )
    crud.create_student_course_interaction(db, student_id=current_student.id, interaction=interaction)

    return progress

@router.get("/playlists", response_model=List[schemas.PlaylistProgress])
def read_student_playlist_progress(
    db: Session = Depends(get_db),
    current_student: schemas.Student = Depends(get_current_student)
):
    """
    Retrieve aggregated playlist progress for the currently authenticated student.
    """
    return crud.get_student_playlist_progress(db, student_id=current_student.id) 