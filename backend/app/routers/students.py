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

@router.put("/me", response_model=schemas.Student)
def update_current_student(
    student_update: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student),
):
    """
    Update the profile of the currently logged-in student.
    """
    return crud.update_student(db=db, student=current_student, student_update=student_update)

@router.post("/me/profile", response_model=schemas.StudentProfile)
def create_or_update_profile_for_current_student(
    profile_data: schemas.StudentProfileCreate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student),
):
    """
    Create or update the profile for the currently logged-in student.
    This is typically used after the onboarding process.
    """
    if current_student.profile:
        # If profile exists, update it
        return crud.update_student_profile(db=db, student=current_student, profile_update=profile_data)
    
    # If profile does not exist, create it
    current_student.has_completed_onboarding = True
    db.add(current_student)
    db.commit()
    db.refresh(current_student)
    
    return crud.create_student_profile(db=db, student_id=current_student.id, profile=profile_data) 