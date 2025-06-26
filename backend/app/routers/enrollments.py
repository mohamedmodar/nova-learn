from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..dependencies import get_db, get_current_student

router = APIRouter(
    prefix="/enrollments",
    tags=["enrollments"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Enrollment)
def enroll_in_course(
    enrollment_request: schemas.EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: models.Student = Depends(get_current_student)
):
    """
    Enrolls the current user in a course.
    """
    course, course_type = crud.get_course_by_id(db, enrollment_request.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{enrollment_request.course_id}' not found."
        )

    # Check if student profile exists
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a student profile. Please create one."
        )
    student_id = current_user.id

    # Check if already enrolled
    existing_enrollment = crud.get_enrollment_by_course_and_student(db, student_id=student_id, course_id=enrollment_request.course_id)
    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already enrolled in this course."
        )

    # Create enrollment
    db_enrollment = crud.create_enrollment(
        db, 
        student_id=student_id, 
        course_id=enrollment_request.course_id, 
        course_type=course_type
    )
    return db_enrollment

@router.get("/me", response_model=List[schemas.Enrollment])
def get_my_enrollments(
    db: Session = Depends(get_db),
    current_user: models.Student = Depends(get_current_student)
):
    """
    Retrieves all course enrollments for the current user.
    """
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a student profile."
        )
    
    student_id = current_user.id
    return crud.get_enrollments_by_student(db, student_id=student_id)

@router.put("/{enrollment_id}", response_model=schemas.Enrollment)
def update_enrollment(
    enrollment_id: int,
    enrollment_update: schemas.EnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: models.Student = Depends(get_current_student)
):
    """
    Updates an enrollment's status or progress.
    """
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a student profile."
        )

    db_enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()

    if not db_enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if db_enrollment.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this enrollment")

    updated_enrollment = crud.update_enrollment_progress(
        db,
        db_enrollment=db_enrollment,
        status=enrollment_update.status,
        progress=enrollment_update.progress
    )
    return updated_enrollment 