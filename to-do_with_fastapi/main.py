from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from models import ToDoDB, UserDB
from typing import Optional

from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJQb29qYW4iLCJleHAiOjE3Njk4OTgyMTV9.crS2D3gF6XSeF-gAUybZ_pQAA7-he4JI2vB9Rrqg_FQ"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def hash_password(password: str):
    return pwd_context.hash(password[:72])


def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

class LoginRequest(BaseModel):
    username: str
    password: str



app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ToDo(BaseModel):
    title : str
    priority : int = Field(ge=1 , le=5)
    status : bool

class ToDoOut(BaseModel):
    id : int
    title : str
    priority : int
    status : bool

    class Config:
        orm_mode = True

class ToDoResponse(BaseModel):
    message : str
    data : ToDoOut

class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=4, max_length=50)



@app.post('/todos', response_model=ToDoResponse)
def add_todo(inp : ToDo, db = Depends(get_db)):
    new_todo = ToDoDB(
        title = inp.title,
        priority = inp.priority,
        status = inp.status
    )

    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)

    return {
        "message" : "new to-do added successfully",
        "new to-do" : new_todo
    }

# @app.get('/todos', response_model=list[ToDoOut])
# def get_todos(
#     status : Optional[bool] = Query(None),
#     limit : int = Query(10, ge=1),
#     offset : int = Query(0, ge=0), 
#     db = Depends(get_db)
# ):
    
#     query = db.query(ToDoDB)
#     if status is not None:
#         query = query.filter(ToDoDB.status == status)

#     todos = query.offset(offset).limit(limit).all()
#     return todos



@app.put('/todos/{id}',response_model=ToDoResponse)
def update_todo(id : int, inp : ToDo, db:Session = Depends(get_db)):
    todo_db = db.query(ToDoDB).filter(ToDoDB.id == id).first()

    if todo_db is None:
        raise HTTPException(
            status_code=404,
            detail= "To-Do not found"
        )
    
    todo_db.title = inp.title
    todo_db.priority = inp.priority
    todo_db.status = inp.status

    db.commit()
    db.refresh(todo_db)

    return {
        "message" : "To-Do updated",
        "Updated_To-Do" : todo_db
    }

@app.delete('/todos/{id}')
def delete_todo(id : int, db:Session = Depends(get_db)):
    todo_db = db.query(ToDoDB).filter(ToDoDB.id == id).first()

    if todo_db is None:
        raise HTTPException(
            status_code=404,
            detail= "To-Do not found"
        )
    
    db.delete(todo_db)
    db.commit()

    return {
        "message" : f"To-Do with id {id} deleted successfully."
    }


@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == data.username).first()
    print(user)
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401)

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None:
        raise HTTPException(status_code=401)

    return user

@app.get("/todos")
def get_todos(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(ToDoDB).all()

@app.post("/create-user")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    print("RAW PASSWORD:", user.password)
    print("TYPE:", type(user.password))
    print("LENGTH:", len(user.password))

    safe_password = str(user.password).strip()[:72]
    print("SAFE LENGTH:", len(safe_password))

    new_user = UserDB(
        username=user.username,
        password=hash_password(safe_password)
    )

    db.add(new_user)
    db.commit()
    return {"message": "user created"}
