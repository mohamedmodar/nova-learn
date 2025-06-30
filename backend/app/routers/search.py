from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from jose import JWTError, jwt

from .. import crud, schemas, models
from .. import dependencies
from ..dependencies import get_db
from ..config import settings

router = APIRouter(
    prefix="/search",
    tags=["search"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

def get_optional_student(request: Request, db: Session = Depends(get_db)) -> Optional[models.Student]:
    """Get current student if authenticated, otherwise return None"""
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
            
        token = auth_header.split(" ")[1]
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
            
        student = crud.get_student_by_email(db, email=email)
        return student
    except (JWTError, AttributeError, IndexError):
        return None

@router.get("/all", response_model=List[schemas.Course])
def search_all_courses(
    query: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.Student] = Depends(get_optional_student)
):
    """
    Search both internal and external courses.
    Logs the search query as a student interaction if user is authenticated.
    """
    # Log the search interaction only if user is authenticated
    if current_user:
        try:
            interaction = schemas.StudentCourseInteractionCreate(
                topic=query,
                interaction_type="search",
                value=3.0  # Use search value from our interaction values
            )
            crud.create_student_course_interaction(db=db, student_id=current_user.id, interaction=interaction)
        except Exception as e:
            # Log the error but don't fail the search
            logging.warning(f"Failed to log search interaction: {e}")

    search_results = crud.search_courses_by_query(db=db, query=query, course_type="all")
    return search_results

@router.get("/external", response_model=List[schemas.Course])
def search_external_courses(
    query: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.Student] = Depends(get_optional_student)
):
    """
    Search only external courses.
    Logs the search query as a student interaction if user is authenticated.
    """
    # Log the search interaction only if user is authenticated
    if current_user:
        try:
            interaction = schemas.StudentCourseInteractionCreate(
                topic=query,
                interaction_type="search",
                value=3.0
            )
            crud.create_student_course_interaction(db=db, student_id=current_user.id, interaction=interaction)
        except Exception as e:
            logging.warning(f"Failed to log search interaction: {e}")

    search_results = crud.search_courses_by_query(db=db, query=query, course_type="external")
    return search_results

@router.get("/internal", response_model=List[schemas.Course])
def search_internal_courses(
    query: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.Student] = Depends(get_optional_student)
):
    """
    Search only internal (YouTube playlist) courses.
    Logs the search query as a student interaction if user is authenticated.
    """
    # Log the search interaction only if user is authenticated
    if current_user:
        try:
            interaction = schemas.StudentCourseInteractionCreate(
                topic=query,
                interaction_type="search",
                value=3.0
            )
            crud.create_student_course_interaction(db=db, student_id=current_user.id, interaction=interaction)
        except Exception as e:
            logging.warning(f"Failed to log search interaction: {e}")

    search_results = crud.search_courses_by_query(db=db, query=query, course_type="internal")
    return search_results 