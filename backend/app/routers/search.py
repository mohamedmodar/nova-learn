from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
import logging

from .. import crud, schemas, models
from .. import dependencies
from ..dependencies import get_db

router = APIRouter(
    prefix="/search",
    tags=["search"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

@router.get("/all", response_model=List[schemas.Course])
def search_all_courses(
    query: str,
    db: Session = Depends(get_db),
    current_user: models.Student = Depends(dependencies.get_current_active_student)
):
    """
    Search both internal and external courses.
    Logs the search query as a student interaction.
    """
    # Log the search interaction
    interaction = schemas.StudentCourseInteractionCreate(
        topic=query,
        interaction_type="search",
        value=1.0  # Use a neutral value for search
    )
    crud.create_student_course_interaction(db=db, student_id=current_user.id, interaction=interaction)

    search_results = crud.search_courses_by_query(db=db, query=query, course_type="all")
    return search_results

@router.get("/external", response_model=List[schemas.Course])
def search_external_courses(
    query: str,
    db: Session = Depends(get_db),
    current_user: models.Student = Depends(dependencies.get_current_active_student)
):
    """
    Search only external courses.
    Logs the search query as a student interaction.
    """
    # Log the search interaction
    interaction = schemas.StudentCourseInteractionCreate(
        topic=query,
        interaction_type="search",
        value=1.0
    )
    crud.create_student_course_interaction(db=db, student_id=current_user.id, interaction=interaction)

    search_results = crud.search_courses_by_query(db=db, query=query, course_type="external")
    return search_results

@router.get("/internal", response_model=List[schemas.Course])
def search_internal_courses(
    query: str,
    db: Session = Depends(get_db),
    current_user: models.Student = Depends(dependencies.get_current_active_student)
):
    """
    Search only internal (YouTube playlist) courses.
    Logs the search query as a student interaction.
    """
    # Log the search interaction
    interaction = schemas.StudentCourseInteractionCreate(
        topic=query,
        interaction_type="search",
        value=1.0
    )
    crud.create_student_course_interaction(db=db, student_id=current_user.id, interaction=interaction)

    search_results = crud.search_courses_by_query(db=db, query=query, course_type="internal")
    return search_results 