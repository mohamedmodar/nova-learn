from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
import google.generativeai as genai
from sqlalchemy.orm import Session
from typing import List, Optional, Union

from ..config import settings
from .. import crud, models, schemas
from ..dependencies import get_db, get_current_student
import logging
import re

# --- Configuration ---
router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"],
)

# Configure the Gemini API client
try:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except (ValueError, AttributeError) as e:
    logging.error(f"Gemini API configuration failed: {e}")
    model = None

# --- Pydantic Schemas ---
class ChatRequest(BaseModel):
    message: str

class CourseRecommendationResponse(schemas.ExternalCourse):
    pass

class ChatResponse(BaseModel):
    response: str
    recommendations: Optional[List[CourseRecommendationResponse]] = None

# --- API Endpoint ---
@router.post("/chat", response_model=ChatResponse)
async def chat_with_nova(
    req: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student),
):
    """
    Handles a chat conversation with the Nova AI assistant.
    If the user's message seems to be asking for courses, it attempts to
    extract skills, get recommendations, and return them.
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured or available."
        )

    # --- Step 1: Extract Skills with Gemini ---
    skill_extraction_prompt = (
        "You are a Skill Extractor. Your task is to identify and extract relevant "
        "technical skills, subjects, or learning topics from the user's query. "
        "Provide the output as a clean, comma-separated list. "
        "For example, if the user says 'I want to learn about web development with python and react', "
        "you should output: 'Web Development, Python, React'. "
        "If no specific skills are found, return an empty string.\n\n"
        f"User Query: \"{chat_request.message}\""
    )

    try:
        logging.info("Sending skill extraction request to Gemini...")
        extraction_response = await model.generate_content_async(skill_extraction_prompt)
        extracted_skills_str = extraction_response.text.strip()
        logging.info(f"Extracted skills string: '{extracted_skills_str}'")

        if extracted_skills_str:
            extracted_skills = [skill.strip() for skill in extracted_skills_str.split(',') if skill.strip()]
            logging.info(f"Chatbot extracted skills: {extracted_skills} for student {current_student.id}")
            for skill in extracted_skills:
                interaction_data = schemas.StudentCourseInteractionCreate(
                    topic=skill,
                    interaction_type='chat_topic'
                )
                crud.create_student_course_interaction(db=db, student_id=current_student.id, interaction=interaction_data)
        else:
            extracted_skills = []

    except Exception as e:
        # We don't want to fail the chat if the background task fails.
        logging.error(f"Error during skill extraction: {e}")
        extracted_skills = [] # Default to empty list on error

    # --- Step 2: If skills are found, get recommendations ---
    if extracted_skills:
        # Get the recommendation function from the app's state
        get_recommendations = req.app.state.get_recommendations
        if get_recommendations is None:
            logging.error("Recommender model not found in app state.")
            # Fall through to default response
        else:
            try:
                # Build query from student's existing profile
                profile_query_parts = []
                if current_student.profile and current_student.profile.learning_goals:
                    profile_query_parts.append(current_student.profile.learning_goals)
                
                profile_query = " ".join(profile_query_parts)
                
                # Combine profile query with extracted skills for a rich query
                final_query_text = f"{profile_query} {' '.join(extracted_skills)}".strip()
                logging.info(f"Constructed Final Query for recommender: '{final_query_text}'")

                # Get user history
                user_interactions = crud.get_student_interactions(db, student_id=current_student.id)
                user_history = [str(i.course_id) for i in user_interactions if i.interaction_type == 'like']
                disliked_history = [str(i.course_id) for i in user_interactions if i.interaction_type == 'dislike']

                # Call the recommendation model
                recommendations_df = get_recommendations(
                    query_text=final_query_text,
                    top_n=5, # Get top 5 courses for the chat
                    user_history=user_history,
                    disliked_history=disliked_history,
                )

                if not recommendations_df.empty:
                    recommended_course_ids = recommendations_df['item_id'].tolist()
                    recommended_courses = crud.get_courses_by_ids(db, course_ids=recommended_course_ids)
                    # Preserve order
                    ordered_courses = sorted(recommended_courses, key=lambda c: recommended_course_ids.index(str(c.item_id)))

                    return ChatResponse(
                        response="Based on your message, I found some courses you might be interested in:",
                        recommendations=ordered_courses
                    )

            except Exception as e:
                logging.error(f"Error getting recommendations in chatbot: {e}")
                # Fall through to the default chat response if recommendation fails

    # --- Step 3: Default to a standard chat response ---
    system_prompt = (
        "You are Nova, a helpful and friendly AI assistant for the NovaLearn learning platform. "
        "Your purpose is to assist users with their learning journey. "
        "You can help them find courses, understand topics, and answer questions about the platform. "
        "Always be encouraging, positive, and supportive. Keep your answers concise and clear."
    )
    
    full_prompt = f"{system_prompt}\n\nUser: {chat_request.message}\nNova:"

    try:
        logging.info("Sending standard chat request to Gemini...")
        response = await model.generate_content_async(full_prompt)
        return ChatResponse(response=response.text)
    except Exception as e:
        logging.error(f"Error communicating with Gemini API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while communicating with the AI assistant."
        ) 