from typing import List
from fastapi import APIRouter, Depends
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