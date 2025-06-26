import sys
import os
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import (
    auth, 
    users, 
    students, 
    courses, 
    recommendations, 
    interactions,
    enrollments,
    search,
    chatbot
)

# Add the model directory to the Python path
# This is a simple way to make the model code importable
# A more robust solution might involve packaging the model as a library
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'model'))

# This creates the tables in the database.
# For production, you would use a migration tool like Alembic.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NovaLearn API",
    description="API for the NovaLearn platform",
    version="0.1.0"
)

# We will store the recommendation function in the app's state
app.state.get_recommendations = None

@app.on_event("startup")
def load_model():
    """
    This function will now attempt to load the model.
    If it fails, it will print a detailed traceback to the console.
    """
    print("Attempting to load recommendation model...")
    try:
        from recommender_interface_advanced_v6 import get_recommendations
        app.state.get_recommendations = get_recommendations
        print(">>> Recommendation model loaded successfully. <<<")
    except Exception as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!   FATAL: FAILED TO LOAD RECOMMENDATION MODEL     !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"--> Exception Type: {type(e).__name__}")
        print(f"--> Exception Details: {e}")
        print("--- Full Traceback ---")
        traceback.print_exc()
        print("----------------------")

# Set up CORS
origins = [
    "http://localhost:5173",  # Default Vite dev server port
    "http://localhost:3000",  # Common React dev server port
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the NovaLearn API"}

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(recommendations.router)
app.include_router(interactions.router)
app.include_router(enrollments.router)
app.include_router(search.router)
app.include_router(chatbot.router)

# Here we will later include the routers for auth, users, courses etc. 