from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, crud, models
from ..dependencies import get_current_student
from ..database import get_db

router = APIRouter(
    prefix="/interactions",
    tags=["Interactions"],
    dependencies=[Depends(get_current_student)],
)

@router.post("/", response_model=schemas.StudentCourseInteraction)
def log_course_interaction(
    interaction_data: schemas.InteractionCreate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student),
):
    """
    Log a student's interaction with a course.

    This endpoint automatically determines the course type (internal/external)
    based on the `course_id`'s data type, validates that the course exists,
    extracts topics from the course, and assigns appropriate values for personalization.
    """
    course_id = interaction_data.course_id
    
    # Determine course type and validate existence
    if isinstance(course_id, str):
        course_type = "external"
        course = crud.get_external_course_by_id(db, course_id=course_id)
    elif isinstance(course_id, int):
        course_type = "internal"
        course = crud.get_internal_course_by_id(db, course_id=course_id)
    else:
        # This case should ideally not be hit due to Pydantic's type validation
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course_id type."
        )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{course_type.capitalize()} course with ID {course_id} not found."
        )

    # Assign a default value if none provided, based on interaction type
    interaction_value = interaction_data.value
    if interaction_value is None:
        interaction_value = crud.get_interaction_value(interaction_data.interaction_type, course)

    # Construct the full interaction object for the database
    full_interaction = schemas.StudentCourseInteractionCreate(
        course_type=course_type,
        course_id=str(course_id), # Ensure course_id is a string for the DB
        interaction_type=interaction_data.interaction_type,
        value=interaction_value  # Now always has a meaningful value
    )
    
    return crud.create_student_course_interaction(
        db=db, student_id=current_student.id, interaction=full_interaction
    ) 