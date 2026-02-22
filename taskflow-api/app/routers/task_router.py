from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.schemas.task_schema import TaskCreate, TaskResponse
from app.services.task_service import create_task, get_all_tasks, delete_task
from typing import List

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskResponse)
def create_task_endpoint(task: TaskCreate, db: Session = Depends(get_db)):
    return create_task(db, task)

@router.get("/", response_model=List[TaskResponse])
def get_tasks_endpoint(db: Session = Depends(get_db)):
    return get_all_tasks(db)

@router.delete("/{task_id}")
def delete_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    task = delete_task(db, task_id)
    if task:
        return {"message": "Task deleted"}
    return {"message": "Task not found"}