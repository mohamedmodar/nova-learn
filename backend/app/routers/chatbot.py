from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
import google.generativeai as genai
from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any
import json

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
    model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Updated to latest model
except (ValueError, AttributeError) as e:
    logging.error(f"Gemini API configuration failed: {e}")
    model = None

# --- Enhanced Pydantic Schemas ---
class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None  # For conversation context

class LearningPathResponse(BaseModel):
    title: str
    steps: List[str]
    estimated_duration: str
    difficulty: str

class StudyPlanResponse(BaseModel):
    goal: str
    weekly_hours: int
    plan: Dict[str, List[str]]  # week -> tasks
    milestones: List[str]

class CourseRecommendationResponse(schemas.ExternalCourse):
    reasoning: Optional[str] = None  # Why this course was recommended

class EnhancedChatResponse(BaseModel):
    response: str
    recommendations: Optional[List[CourseRecommendationResponse]] = None
    learning_path: Optional[LearningPathResponse] = None
    study_plan: Optional[StudyPlanResponse] = None
    suggested_actions: Optional[List[str]] = None
    follow_up_questions: Optional[List[str]] = None

# --- Helper Functions ---
def get_user_context(db: Session, student: models.Student) -> str:
    """Build comprehensive user context for better responses"""
    context_parts = []
    
    # Profile information
    if student.profile:
        profile = student.profile
        context_parts.append(f"Learning Goals: {profile.learning_goals or 'Not specified'}")
        context_parts.append(f"English Proficiency: {profile.english_proficiency or 'Unknown'}/10")
        context_parts.append(f"Math Proficiency: {profile.math_proficiency or 'Unknown'}/10")
        context_parts.append(f"Weekly Time: {profile.weekly_time_commitment or 'Unknown'} hours")
        context_parts.append(f"Preferred Format: {profile.learning_format_preference or 'Any'}")
        
        if profile.technical_skills:
            skills = ', '.join(profile.technical_skills) if isinstance(profile.technical_skills, list) else str(profile.technical_skills)
            context_parts.append(f"Technical Skills: {skills}")
    
    # Recent interactions
    recent_interactions = crud.get_student_interactions(db, student_id=student.id)
    if recent_interactions:
        liked_topics = [i.topic for i in recent_interactions[-10:] if i.interaction_type == 'like' and i.topic]
        searched_topics = [i.topic for i in recent_interactions[-10:] if i.interaction_type == 'search' and i.topic]
        
        if liked_topics:
            context_parts.append(f"Recently Liked Topics: {', '.join(set(liked_topics))}")
        if searched_topics:
            context_parts.append(f"Recent Searches: {', '.join(set(searched_topics))}")
    
    return " | ".join(context_parts)

async def analyze_intent(message: str, user_context: str) -> Dict[str, Any]:
    """Use Gemini to analyze user intent and determine response type"""
    intent_prompt = f"""
    You are an advanced educational AI. Analyze this user message and determine the best response type.
    
    User Context: {user_context}
    User Message: "{message}"
    
    Determine the intent and respond with JSON in this exact format:
    {{
        "intent": "course_recommendation|learning_path|study_plan|concept_explanation|progress_check|general_question",
        "confidence": 0.0-1.0,
        "extracted_skills": ["skill1", "skill2"],
        "difficulty_level": "beginner|intermediate|advanced",
        "time_commitment": "estimated hours per week",
        "specific_topic": "main topic if any",
        "requires_recommendations": true/false,
        "suggested_response_type": "conversational|structured|action_oriented"
    }}
    """
    
    try:
        response = await model.generate_content_async(intent_prompt)
        # Clean the response to extract JSON
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:-3]
        elif text.startswith('```'):
            text = text[3:-3]
        
        return json.loads(text)
    except Exception as e:
        logging.error(f"Intent analysis failed: {e}")
        return {
            "intent": "general_question",
            "confidence": 0.5,
            "extracted_skills": [],
            "requires_recommendations": False,
            "suggested_response_type": "conversational"
        }

# --- Enhanced API Endpoint ---
@router.post("/chat", response_model=EnhancedChatResponse)
async def chat_with_nova(
    req: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student),
):
    """
    Enhanced chat with Nova AI - provides personalized learning assistance,
    course recommendations, study plans, and learning paths.
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured or available."
        )

    # Build user context
    user_context = get_user_context(db, current_student)
    
    # Analyze user intent
    intent_data = await analyze_intent(chat_request.message, user_context)
    
    # Log extracted skills
    if intent_data.get("extracted_skills"):
        for skill in intent_data["extracted_skills"]:
            interaction_data = schemas.StudentCourseInteractionCreate(
                topic=skill,
                interaction_type='chat_topic',
                value=4.0
            )
            crud.create_student_course_interaction(
                db=db, student_id=current_student.id, interaction=interaction_data
            )

    # Generate response based on intent
    response = await generate_enhanced_response(
        req, db, current_student, chat_request.message, 
        intent_data, user_context
    )
    
    return response

async def generate_enhanced_response(
    req: Request,
    db: Session,
    student: models.Student,
    message: str,
    intent_data: Dict[str, Any],
    user_context: str
) -> EnhancedChatResponse:
    """Generate enhanced response based on analyzed intent"""
    
    intent = intent_data.get("intent", "general_question")
    
    if intent == "course_recommendation" and intent_data.get("requires_recommendations", False):
        return await generate_course_recommendations(req, db, student, message, intent_data, user_context)
    
    elif intent == "learning_path":
        return await generate_learning_path(message, intent_data, user_context)
    
    elif intent == "study_plan":
        return await generate_study_plan(message, intent_data, user_context)
    
    elif intent == "concept_explanation":
        return await generate_concept_explanation(message, intent_data, user_context)
    
    else:
        return await generate_conversational_response(message, user_context)

async def generate_course_recommendations(
    req: Request, db: Session, student: models.Student, 
    message: str, intent_data: Dict, user_context: str
) -> EnhancedChatResponse:
    """Generate course recommendations with reasoning"""
    
    # Get recommendations using existing system
    get_recommendations = req.app.state.get_recommendations
    if get_recommendations:
        try:
            skills = intent_data.get("extracted_skills", [])
            query_text = f"{message} {' '.join(skills)}"
            
            user_interactions = crud.get_student_interactions(db, student_id=student.id)
            user_history = [str(i.course_id) for i in user_interactions if i.interaction_type == 'like']
            disliked_history = [str(i.course_id) for i in user_interactions if i.interaction_type == 'dislike']

            recommendations_df = get_recommendations(
                query_text=query_text,
                top_n=5,
                user_history=user_history,
                disliked_history=disliked_history,
            )

            if not recommendations_df.empty:
                recommended_course_ids = recommendations_df['item_id'].tolist()
                courses = crud.get_courses_by_ids(db, course_ids=recommended_course_ids)
                
                # Add reasoning for each recommendation
                enhanced_courses = []
                for course in courses:
                    enhanced_courses.append(CourseRecommendationResponse(
                        **course.__dict__,
                        reasoning=f"Matches your interest in {', '.join(skills[:2])} and aligns with your learning goals"
                    ))

                return EnhancedChatResponse(
                    response=f"Based on your interest in {', '.join(skills)}, I found these courses that match your profile:",
                    recommendations=enhanced_courses,
                    suggested_actions=[
                        "Click on a course to learn more",
                        "Like courses that interest you for better recommendations",
                        "Ask me to create a learning path for your goals"
                    ],
                    follow_up_questions=[
                        "Would you like me to create a study plan for these topics?",
                        "Do you need help understanding any specific concepts?",
                        "What's your target timeline for learning this?"
                    ]
                )
        except Exception as e:
            logging.error(f"Error in course recommendations: {e}")
    
    # Fallback response
    return await generate_conversational_response(message, user_context)

async def generate_learning_path(message: str, intent_data: Dict, user_context: str) -> EnhancedChatResponse:
    """Generate a structured learning path"""
    
    prompt = f"""
    Create a detailed learning path based on this request:
    Message: "{message}"
    User Context: {user_context}
    Difficulty Level: {intent_data.get('difficulty_level', 'intermediate')}
    
    Respond with a structured learning path including:
    1. Clear title
    2. Step-by-step progression (5-8 steps)
    3. Estimated time for completion
    4. Prerequisites if any
    5. Practical projects or milestones
    
    Make it specific and actionable for a {intent_data.get('difficulty_level', 'intermediate')} learner.
    """
    
    try:
        response = await model.generate_content_async(prompt)
        
        # Parse response into structured format
        # For now, return a conversational response with structured guidance
        return EnhancedChatResponse(
            response=response.text,
            suggested_actions=[
                "Search for courses covering each step",
                "Set weekly learning goals",
                "Track your progress regularly"
            ],
            follow_up_questions=[
                "Which step would you like to start with?",
                "Do you need course recommendations for any specific step?",
                "Would you like me to create a weekly study schedule?"
            ]
        )
        
    except Exception as e:
        logging.error(f"Error generating learning path: {e}")
        return await generate_conversational_response(message, user_context)

async def generate_study_plan(message: str, intent_data: Dict, user_context: str) -> EnhancedChatResponse:
    """Generate a personalized study plan"""
    
    prompt = f"""
    Create a personalized study plan based on:
    Request: "{message}"
    User Context: {user_context}
    Available Time: {intent_data.get('time_commitment', 'flexible')} per week
    
    Include:
    1. Weekly breakdown of activities
    2. Specific goals for each week
    3. Time allocation for different types of learning
    4. Milestones and checkpoints
    5. Flexibility for different learning styles
    
    Make it realistic and achievable.
    """
    
    try:
        response = await model.generate_content_async(prompt)
        
        return EnhancedChatResponse(
            response=response.text,
            suggested_actions=[
                "Set calendar reminders for study sessions",
                "Find courses that match your weekly goals",
                "Join study groups or forums for motivation"
            ],
            follow_up_questions=[
                "Would you like help finding courses for this plan?",
                "Do you need tips for staying motivated?",
                "Should I adjust the plan based on your schedule?"
            ]
        )
        
    except Exception as e:
        logging.error(f"Error generating study plan: {e}")
        return await generate_conversational_response(message, user_context)

async def generate_concept_explanation(message: str, intent_data: Dict, user_context: str) -> EnhancedChatResponse:
    """Provide detailed concept explanations"""
    
    topic = intent_data.get("specific_topic", "the requested topic")
    level = intent_data.get("difficulty_level", "intermediate")
    
    prompt = f"""
    You are an expert educator. Explain this concept clearly:
    
    Topic: "{message}"
    User Level: {level}
    User Context: {user_context}
    
    Provide:
    1. Clear, simple explanation
    2. Real-world examples
    3. Common misconceptions to avoid
    4. How it connects to other concepts
    5. Practical applications
    
    Adapt the complexity to the user's {level} level.
    """
    
    try:
        response = await model.generate_content_async(prompt)
        
        return EnhancedChatResponse(
            response=response.text,
            suggested_actions=[
                f"Search for courses about {topic}",
                "Practice with hands-on exercises",
                "Join discussion forums on this topic"
            ],
            follow_up_questions=[
                f"Would you like course recommendations for {topic}?",
                "Do you want to see related concepts?",
                "Need help with any specific part of this explanation?"
            ]
        )
        
    except Exception as e:
        logging.error(f"Error generating concept explanation: {e}")
        return await generate_conversational_response(message, user_context)

async def generate_conversational_response(message: str, user_context: str) -> EnhancedChatResponse:
    """Generate general conversational response"""
    
    system_prompt = f"""
    You are Nova, an advanced AI learning assistant for NovaLearn platform. You help students achieve their educational goals.
    
    User Context: {user_context}
    
    Guidelines:
    - Be encouraging and supportive
    - Provide actionable advice
    - Reference their learning goals when relevant
    - Suggest specific actions they can take
    - Keep responses concise but helpful
    - Always look for ways to guide them toward learning opportunities
    """
    
    full_prompt = f"{system_prompt}\n\nUser: {message}\nNova:"
    
    try:
        response = await model.generate_content_async(full_prompt)
        
        return EnhancedChatResponse(
            response=response.text,
            suggested_actions=[
                "Explore the course catalog",
                "Update your learning goals",
                "Check your progress dashboard"
            ],
            follow_up_questions=[
                "What would you like to learn next?",
                "Do you need help finding specific courses?",
                "Would you like study tips for your current goals?"
            ]
        )
        
    except Exception as e:
        logging.error(f"Error in conversational response: {e}")
        return EnhancedChatResponse(
            response="I'm here to help with your learning journey! What would you like to know about?",
            suggested_actions=["Explore courses", "Ask me about any topic"]
        ) 