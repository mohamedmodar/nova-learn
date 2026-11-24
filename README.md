# NovaLearn — Personalized Learning Platform

NovaLearn is an AI-powered learning platform designed to help learners discover relevant courses and build personalized learning paths based on their goals, skills, preferences, and learning activity.

The platform combines a full-stack web application with multiple recommendation approaches and an AI-powered learning assistant to provide a more personalized learning experience.

## Overview

Finding the right learning resources can be difficult when learners have different backgrounds, skill levels, and goals.

NovaLearn addresses this problem by combining learner profiles, course information, and user interactions to generate personalized course recommendations.

The platform also provides course discovery, enrollment tracking, learning progress management, and an AI assistant to support learners throughout their journey.

## Key Features

### Personalized Course Recommendations
- Multiple recommendation approaches: TF-IDF, SBERT, Two-Tower, and Hybrid.
- Recommendations informed by learner profiles, technical skills, learning goals, and interaction history.
- Support for different course preferences and recommendation strategies.

### Learning Management
- Browse internal and external learning resources.
- Search and explore available courses.
- Enroll in courses and track learning progress.
- Manage learner profiles and learning preferences.

### AI Learning Assistant
- Gemini-powered conversational assistant.
- Learning path suggestions.
- Study plan generation.
- Context-aware responses based on learner information.

### Authentication
- User registration and login.
- JWT-based authentication.
- Password hashing.
- Protected API endpoints.

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| UI | Tailwind CSS, shadcn/ui, Radix UI |
| Backend | Python, FastAPI |
| Database | PostgreSQL, SQLAlchemy |
| Recommendation System | Python, Pandas, NumPy, Scikit-learn |
| NLP & Embeddings | TF-IDF, Sentence-BERT |
| Deep Learning | PyTorch, TensorFlow |
| Authentication | JWT, Passlib, bcrypt |
| AI Assistant | Google Gemini API |

## System Architecture

NovaLearn consists of three main components:

```text
                  ┌─────────────────────────┐
                  │      React Frontend     │
                  │       TypeScript        │
                  └────────────┬────────────┘
                               │
                         HTTP / REST API
                               │
                  ┌────────────▼────────────┐
                  │      FastAPI Backend    │
                  │                         │
                  │  Authentication         │
                  │  Course Management      │
                  │  User Interactions      │
                  │  Recommendations        │
                  │  Learning Progress      │
                  │  AI Chatbot             │
                  └───────┬─────────┬───────┘
                          │         │
                ┌─────────▼───┐ ┌───▼────────────────┐
                │ PostgreSQL  │ │ Recommendation     │
                │ Database    │ │ Engine             │
                └─────────────┘ │ TF-IDF / SBERT     │
                                │ Two-Tower / Hybrid  │
                                └────────────────────┘
```

### Recommendation Approaches

The recommendation engine combines several approaches:

| Model | Description |
|---|---|
| TF-IDF | Content-based recommendations using textual features. |
| SBERT | Semantic similarity using sentence embeddings. |
| Two-Tower | Neural recommendation approach using learner and course representations. |
| Hybrid | Combines recommendation strategies to improve personalization. |

The backend uses learner information and interaction history to construct recommendation inputs and retrieve matching courses.

## Project Structure

```text
nova-learn/
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── chatbot.py
│   │   │   ├── courses.py
│   │   │   ├── enrollments.py
│   │   │   ├── interactions.py
│   │   │   ├── progress.py
│   │   │   ├── recommendations.py
│   │   │   ├── search.py
│   │   │   └── students.py
│   │   ├── config.py
│   │   ├── crud.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── security.py
│   ├── requirements.txt
│   └── ENVIRONMENT.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── pages/
│   │   └── ...
│   ├── package.json
│   └── package-lock.json
│
├── model/
│   ├── models/
│   ├── adapted_two_tower_model.py
│   ├── recommender_interface_advanced_v6.py
│   ├── hybrid_recommender_logic.py
│   └── ...
│
└── README.md
```

## Getting Started

### Prerequisites

Make sure you have the following installed:

- Node.js and npm
- Python 3.10 or a compatible version for the project's dependencies
- PostgreSQL
- Git

You will also need a Google Gemini API key to use the AI assistant.

### 1. Clone the Repository

```bash
git clone https://github.com/mohamedmodar/nova-learn.git
cd nova-learn
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file inside the `backend/` directory.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/novalearn

SECRET_KEY=replace_with_a_strong_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

GEMINI_API_KEY=your_gemini_api_key
```

Replace the database credentials and API key with your own values.

Create the PostgreSQL database before starting the backend.

**Security:** Never commit your `.env` file or expose your API keys and secret values.

### 4. Recommendation Model Assets

The recommendation engine requires its trained model artifacts and course dataset.

The current implementation expects resources including:

- `model/models/tfidf_vectorizer.pkl`
- `model/models/tfidf_matrix.pkl`
- `model/models/course_sbert_embeddings.pkl`
- `model/models/two_tower_content_based.weights.h5`
- `model/data/final(final).csv`

Make sure these files are available in their expected locations before using the recommendation endpoints.

Large model artifacts and datasets should be distributed separately when necessary, with clear download and setup instructions.

### 5. Run the Backend

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Frontend Setup

Open another terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Vite will display the local development URL in the terminal.

Make sure the frontend API configuration points to the running backend.

## API Overview

The backend exposes RESTful endpoints organized into several routers:

| Area | Responsibility |
|---|---|
| `/auth` | Registration and authentication |
| `/students` | Student profiles and learner information |
| `/courses` | Internal and external course resources |
| `/recommendations` | Personalized course recommendations |
| `/interactions` | Learner interactions and preferences |
| `/enrollments` | Course enrollment management |
| `/progress` | Learning progress tracking |
| `/search` | Course discovery and search |
| `/chatbot` | AI-powered learning assistant |

For detailed request and response schemas, run the backend and visit `/docs`.

## Current Development Status

NovaLearn is an ongoing project. The core application structure and major platform features have been implemented, while some engineering and deployment improvements remain part of the development roadmap.

Planned improvements include:

- Expanding automated backend and frontend test coverage.
- Database schema migrations and version management.
- Improving API validation, security, and error handling.
- Containerization with Docker and Docker Compose.
- CI/CD automation and deployment.
- Improving recommendation model integration and evaluation.

## Future Directions

- More advanced learner behavior modeling.
- Improved cold-start recommendation strategies.
- Recommendation explainability.
- Learning analytics and progress insights.
- Scalable model serving and background processing.

## License

This project currently includes a license file in the model directory. Repository-wide licensing and attribution should be clarified before distributing the complete platform.

---

**NovaLearn** — Making learning more personalized, structured, and accessible.
