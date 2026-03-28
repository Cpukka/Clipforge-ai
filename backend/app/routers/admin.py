from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.utils.auth import require_role
from typing import List

router = APIRouter()

@router.get("/users", response_model=List[schemas.UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role("admin"))
):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/jobs")
async def get_processing_jobs(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_role("admin"))
):
    jobs = db.query(models.ProcessingJob).all()
    return jobs