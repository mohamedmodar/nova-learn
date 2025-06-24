from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, models, crud
from ..dependencies import get_current_student
from ..database import get_db

router = APIRouter(
    prefix="/students",
    tags=["Students"],
    dependencies=[Depends(get_current_student)],
)

@router.get("/me", response_model=schemas.Student)
def read_current_student(current_student: models.Student = Depends(get_current_student)):
    """
    Get the profile of the currently logged-in student.
    """
    return current_student

@router.post("/me/profile", response_model=schemas.StudentProfile)
def create_profile_for_current_student(
    profile_data: schemas.StudentProfileCreate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student),
):
    """
    Create or update the profile for the currently logged-in student.
    This is typically used after the onboarding process.
    """
    if current_student.profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists for this student.",
        )
    
    # We can add logic here to update the student model as well, e.g.,
    # current_student.has_completed_onboarding = True
    # db.commit()
    
    return crud.create_student_profile(db=db, student_id=current_student.id, profile=profile_data) 