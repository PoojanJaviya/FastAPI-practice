from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta

from database import SessionLocal
from models import UserDB, NoteDB  
from database import engine
from models import Base
from passlib.context import CryptContext

Base.metadata.create_all(bind=engine)
 # you create these

app = FastAPI()

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str):
    return pwd_context.hash(password[:72])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password[:72], hashed_password)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=4, max_length=50)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)

    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None:
        raise HTTPException(status_code=401)

    return user


@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == data.username).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/my-notes")
def read_my_notes(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notes = db.query(NoteDB).filter(
        NoteDB.owner_id == current_user.id
    ).all()

    return notes

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