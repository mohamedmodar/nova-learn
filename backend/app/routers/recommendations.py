from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import pandas as pd

from .. import schemas, crud, models
from ..dependencies import get_current_student
from ..database import get_db

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
    dependencies=[Depends(get_current_student)],
)

@router.post("/", response_model=List[schemas.ExternalCourse])
def get_course_recommendations(
    # By moving the body (`request_data`) to the end and making it
    # optional, we allow for completely empty requests.
    request: Request,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student),
    request_data: Optional[schemas.RecommendationRequest] = None
):
    """
    Get personalized course recommendations for the current student.
    An empty request body is allowed.
    """
    # If the request body is empty, create a default object to use.
    if request_data is None:
        request_data = schemas.RecommendationRequest()

    # Get the recommendation function from the app's state
    get_recommendations = request.app.state.get_recommendations
    
    if get_recommendations is None:
        raise HTTPException(status_code=503, detail="Recommendation model is not available. Check server logs for details.")

    print("\n--- [API] New Recommendation Request ---")
    print(f"[API] Request Body: {request_data.dict()}")

    # 1. Build a query from the student's profile
    profile_query_parts = []
    if current_student.profile:
        print("[API] Found student profile. Building query from it.")
        if current_student.profile.learning_goals:
            profile_query_parts.append(current_student.profile.learning_goals)
        if current_student.profile.technical_skills:
            # Assuming technical_skills is a list of strings
            profile_query_parts.extend(current_student.profile.technical_skills)
    
    # The primary query text comes from the user's profile
    profile_query = " ".join(profile_query_parts)
    # The query from the request is used to refine the search
    final_query_text = f"{profile_query} {request_data.query_text or ''}".strip()
    print(f"[API] Constructed Final Query: '{final_query_text}'")

    # 2. Get user history from the database
    user_interactions = crud.get_student_interactions(db, student_id=current_student.id)
    
    user_history = [
        str(i.course_id) for i in user_interactions if i.interaction_type == 'like'
    ]
    disliked_history = [
        str(i.course_id) for i in user_interactions if i.interaction_type == 'dislike'
    ]
    print(f"[API] User History (Likes): {user_history}")
    print(f"[API] User History (Dislikes): {disliked_history}")

    # 3. Call the recommendation model
    try:
        print("[API] Calling the recommendation model...")
        recommendations_df = get_recommendations(
            query_text=final_query_text,
            level=request_data.level,
            skills=request_data.skills,
            providers=request_data.providers,
            top_n=request_data.top_n,
            user_history=user_history,
            disliked_history=disliked_history,
            model_type=request_data.model_type,
            duration_pref=request_data.duration_pref
        )
        
        print(f"[API] Model returned a DataFrame with {len(recommendations_df)} rows.")
        if not recommendations_df.empty:
            print("[API] Model Output (DataFrame Head):")
            print(recommendations_df.head())
        
        if recommendations_df.empty:
            print("[API] DataFrame is empty. Returning [].")
            return []

        # 4. Get course details from the database based on recommended IDs
        recommended_course_ids = recommendations_df['item_id'].tolist()
        print(f"[API] Extracted Course IDs: {recommended_course_ids}")
        
        recommended_courses = crud.get_courses_by_ids(db, course_ids=recommended_course_ids)
        print(f"[API] Found {len(recommended_courses)} courses in the database from the list of IDs.")
        
        # Preserve the order from the recommendation model
        ordered_courses = sorted(recommended_courses, key=lambda c: recommended_course_ids.index(str(c.item_id)))
        print(f"[API] Final ordered list contains {len(ordered_courses)} courses.")
        print("--- [API] Request Complete ---\n")

        return ordered_courses

    except Exception as e:
        # Log the exception for debugging
        print(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve recommendations.") 