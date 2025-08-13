from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func  # Added for case-insensitive search
import logging
from datetime import datetime
import models
from database import SessionLocal, engine
import hashlib
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class QuestionCreate(BaseModel):
    question: str
    answer: bool

class QuizSubmission(BaseModel):
    username: str
    answers: List[bool]

class AuthRequest(BaseModel):
    username: str
    password: str
    tenant: str

class TenantCreate(BaseModel):
    name: str
    display_name: str

# Helper function to hash passwords
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Tenant endpoints
@app.post("/tenant/create")
def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    # Normalize tenant name
    tenant_name = tenant.name.strip().lower()
    
    # Check if tenant already exists (case-insensitive)
    db_tenant = db.query(models.Tenant).filter(
        func.lower(models.Tenant.name) == tenant_name
    ).first()
    
    if db_tenant:
        raise HTTPException(
            status_code=400,
            detail=f"Tenant '{tenant.name}' already exists"
        )
    
    new_tenant = models.Tenant(
        name=tenant.name.strip(),
        display_name=tenant.display_name.strip()
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    return {
        "message": "Tenant created successfully",
        "tenant_id": new_tenant.id,
        "name": new_tenant.name
    }

# Tenant verification endpoint
@app.get("/tenant-check/{tenant_name}")
def check_tenant(tenant_name: str, db: Session = Depends(get_db)):
    tenant = db.query(models.Tenant).filter(
        func.lower(models.Tenant.name) == tenant_name.strip().lower()
    ).first()
    return {"exists": tenant is not None}

@app.post("/signup")
def signup(auth: AuthRequest, db: Session = Depends(get_db)):
    # Normalize inputs
    tenant_name = auth.tenant.strip().lower()
    username = auth.username.strip()
    
    # 1. Find tenant
    tenant = db.query(models.Tenant).filter(
        func.lower(models.Tenant.name) == tenant_name
    ).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # 2. Check if username exists IN THIS SPECIFIC TENANT ONLY
    existing_user = db.query(models.User).filter(
        func.lower(models.User.username) == username.lower(),
        models.User.tenant_id == tenant.id  # This is the critical part
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists in this tenant"
        )
    
    # 3. Create user (same username can exist in other tenants)
    new_user = models.User(
        username=username,
        password=hash_password(auth.password.strip()),
        tenant_id=tenant.id
    )
    db.add(new_user)
    db.commit()
    
    return {
        "message": "Signup successful",
        "tenant": tenant.name,
        "username": username
    }
@app.post("/login")
def login(auth: AuthRequest, db: Session = Depends(get_db)):
    # Normalize inputs
    tenant_name = auth.tenant.strip().lower()
    username = auth.username.strip()
    
    # Find tenant
    tenant = db.query(models.Tenant).filter(
        func.lower(models.Tenant.name) == tenant_name
    ).first()
    
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    # Find user
    user = db.query(models.User).filter(
        func.lower(models.User.username) == username.lower(),
        models.User.tenant_id == tenant.id
    ).first()
    
    # Verify credentials
    if not user or user.password != hash_password(auth.password.strip()):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    logger.info(f"Successful login - Tenant: {tenant.name} | User: {username}")
    return {"message": "Login successful"}

# Admin endpoints
@app.post("/{tenant}/admin/set_questions")
def set_questions(
    tenant: str,
    payload: Dict[str, List[QuestionCreate]],
    db: Session = Depends(get_db)
):
    # Find tenant
    db_tenant = db.query(models.Tenant).filter(
        func.lower(models.Tenant.name) == tenant.strip().lower()
    ).first()
    
    if not db_tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    # Check for existing questions
    existing_questions = db.query(models.Question).filter(
        models.Question.tenant_id == db_tenant.id
    ).count()
    
    if existing_questions > 0:
        questions = db.query(models.Question).filter(
            models.Question.tenant_id == db_tenant.id
        ).all()
        return {
            "message": "Questions already exist for this tenant",
            "questions": [{
                "id": q.id,
                "question": q.question,
                "answer": q.answer
            } for q in questions]
        }
    
    # Add new questions
    for q in payload["questions"]:
        question = models.Question(
            question=q.question.strip(),
            answer=q.answer,
            tenant_id=db_tenant.id
        )
        db.add(question)
    
    db.commit()
    logger.info(f"Admin set questions - Tenant: {db_tenant.name}")
    return {"message": f"{len(payload['questions'])} questions set for {db_tenant.name}"}

# Student endpoints
@app.get("/{tenant}/student/questions")
def get_questions(tenant: str, db: Session = Depends(get_db)):
    # Find tenant
    db_tenant = db.query(models.Tenant).filter(
        func.lower(models.Tenant.name) == tenant.strip().lower()
    ).first()
    
    if not db_tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    questions = db.query(models.Question).filter(
        models.Question.tenant_id == db_tenant.id
    ).all()
    
    return [{"id": q.id, "question": q.question} for q in questions]
# Add this to your FastAPI backend (main.py)
@app.get("/{tenant}/admin/questions")
def get_admin_questions(tenant: str, db: Session = Depends(get_db)):
    db_tenant = db.query(models.Tenant).filter(
        func.lower(models.Tenant.name) == tenant.strip().lower()
    ).first()
    
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    questions = db.query(models.Question).filter(
        models.Question.tenant_id == db_tenant.id
    ).all()
    
    return [{"id": q.id, "question": q.question, "answer": q.answer} for q in questions]

@app.post("/{tenant}/student/submit")
def submit_quiz(
    tenant: str,
    submission: QuizSubmission,
    db: Session = Depends(get_db)
):
    # Find tenant
    db_tenant = db.query(models.Tenant).filter(
        func.lower(models.Tenant.name) == tenant.strip().lower()
    ).first()
    
    if not db_tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    # Find user
    user = db.query(models.User).filter(
        func.lower(models.User.username) == submission.username.strip().lower(),
        models.User.tenant_id == db_tenant.id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Get questions
    questions = db.query(models.Question).filter(
        models.Question.tenant_id == db_tenant.id
    ).all()
    
    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No questions found for this tenant"
        )
    
    # Calculate score
    correct = sum(
        1 for i, q in enumerate(questions) 
        if i < len(submission.answers) and q.answer == submission.answers[i]
    )
    
    # Record submission
    new_submission = models.QuizSubmission(
        answers=submission.answers,
        score=correct,
        user_id=user.id,
        tenant_id=db_tenant.id
    )
    db.add(new_submission)
    db.commit()
    
    logger.info(f"Quiz submitted - Tenant: {db_tenant.name} | User: {user.username} | Score: {correct}/{len(questions)}")
    return {
        "message": f"You scored {correct}/{len(questions)}",
        "username": user.username,
        "score": correct,
        "total": len(questions)
    }