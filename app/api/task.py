from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_current_user
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["Tasks"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return db.query(Task).all()

@router.get("/user/{user_id}", response_model=list[TaskResponse])
def get_user_tasks(
    user_id: int,
    db: Session = Depends(get_db)
):
    return db.query(Task).filter(Task.user_id == user_id).all()

@router.get("/me", response_model=list[TaskResponse])
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return db.query(Task).filter(Task.user_id == current_user.id).all()