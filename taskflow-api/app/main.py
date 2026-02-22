from fastapi import FastAPI
from app.db.session import engine, Base
from app.models import task_model 

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "TaskFlow API is running"}