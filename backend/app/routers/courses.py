from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, crud
from ..database import get_db

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)

@router.get("/internal", response_model=List[schemas.InternalCourse])
def read_internal_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of internal courses.
    """
    courses = crud.get_internal_courses(db, skip=skip, limit=limit)
    return courses

@router.get("/external", response_model=List[schemas.ExternalCourse])
def read_external_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of external courses.
    """
    courses = crud.get_external_courses(db, skip=skip, limit=limit)
    return courses

@router.get("/{course_id}", response_model=Union[schemas.ExternalCourse, schemas.InternalCourse])
def read_course_by_id(course_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a single course by its ID.
    The endpoint automatically handles both internal (integer) and external (string) course IDs.
    """
    # First, try to find an external course with the given ID.
    course = crud.get_external_course_by_id(db, course_id=course_id)
    if course:
        return course
    
    # If no external course is found, try to treat the ID as an integer and find an internal course.
    try:
        internal_course_id = int(course_id)
        course = crud.get_internal_course_by_id(db, course_id=internal_course_id)
        if course:
            return course
    except ValueError:
        # The ID is not a valid integer, so it can't be an internal course ID.
        pass

    # If no course is found in either table, raise a 404 error.
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Course with ID '{course_id}' not found."
    ) 