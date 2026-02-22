from fastapi import FastAPI
from app.db.session import engine, Base
from app.models import task_model
from app.routers.task_router import router as task_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(task_router)

@app.get("/")
def root():
    return {"message": "TaskFlow API is running"}