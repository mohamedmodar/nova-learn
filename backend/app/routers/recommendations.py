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

    # 1. Build a rich query from multiple sources
    profile_query_parts = []
    
    # Source A: Student's permanent profile
    if current_student.profile:
        print("[API] Found student profile. Adding to query.")
        if current_student.profile.learning_goals:
            profile_query_parts.append(current_student.profile.learning_goals)
        if current_student.profile.technical_skills:
            profile_query_parts.extend(current_student.profile.technical_skills)
    
    # Source B: Student's recent interactions (search and chat topics)
    all_interactions = crud.get_student_interactions(db, student_id=current_student.id)
    
    # Separate learned topics from course likes/dislikes
    learned_topics = [i.topic for i in all_interactions if i.topic]
    if learned_topics:
        learned_topics_str = " ".join(learned_topics)
        profile_query_parts.append(learned_topics_str)
        print(f"[API] Found {len(learned_topics)} learned topics from interactions. Adding to query.")

    # Source C: The query from the request body (for specific, one-off searches)
    if request_data.query_text:
        profile_query_parts.append(request_data.query_text)
        print(f"[API] Found ad-hoc query text: '{request_data.query_text}'. Adding to query.")

    # Combine all sources into the final query
    final_query_text = " ".join(profile_query_parts).strip()
    print(f"[API] Constructed Final Rich Query: '{final_query_text}'")

    # 2. Get user history from the database (likes and dislikes for specific courses)
    user_history = [
        str(i.course_id) for i in all_interactions if i.interaction_type == 'like' and i.course_id
    ]
    disliked_history = [
        str(i.course_id) for i in all_interactions if i.interaction_type == 'dislike' and i.course_id
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