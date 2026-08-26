from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, TaskDB, engine, Base
from pydantic import BaseModel, Field
from typing import Optional

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Task Manager API",
    description="Учебный API для управления задачами. Поддерживает полный CRUD с хранением в PostgreSQL.",
    version="1.0.0"
)

class Task(BaseModel):
    title: str
    completed: bool = False

#tasks = []  # хранилище в памяти — обычный список словарей

class TaskCreate(BaseModel):
    title: str
    completed: bool = False

class TaskResponse(BaseModel):
    id: int
    title: str = Field(..., example="Купить продукты")
    completed: bool

    class Config:
        from_attributes = True  # позволяет строить модель из ORM-объекта (TaskDB), а не только из словаря

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post(
    "/tasks", 
    status_code=201, 
    summary="Создать задачу",
    response_model=list[TaskResponse],
    tags=["Tasks"]
    )
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = TaskDB(title=task.title, completed=task.completed)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.get(
    "/tasks",
    response_model=list[TaskResponse],
    tags=["Tasks"]
)
def get_tasks(db: Session = Depends(get_db)):
    return db.query(TaskDB).all()

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

@app.patch(
    "/tasks/{task_id}", 
    tags=["Tasks"],
    responses={
        404: {"description": "Задача с указанным ID не найдена"}
    }
    )
def update_task_partial(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task

@app.delete(
    "/tasks/{task_id}", 
    status_code=204, 
    tags=["Tasks"],
    responses={
        404: {"description": "Задача с указанным ID не найдена"}
    }
    )
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()

@app.put(
    "/tasks/{task_id}", 
    tags=["Tasks"],
        responses={
        404: {"description": "Задача с указанным ID не найдена"}
    }
    )
def update_task_full(task_id: int, task: TaskCreate, db: Session = Depends(get_db)):
    existing_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    existing_task.title = task.title
    existing_task.completed = task.completed
    db.commit()
    db.refresh(existing_task)
    return existing_task
