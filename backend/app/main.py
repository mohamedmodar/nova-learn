from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import auth, users, courses, students

# This creates the tables in the database.
# For production, you would use a migration tool like Alembic.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NovaLearn API",
    description="API for the NovaLearn platform",
    version="0.1.0"
)

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
app.include_router(courses.router)
app.include_router(students.router)

# Here we will later include the routers for auth, users, courses etc. 