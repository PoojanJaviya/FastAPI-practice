from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from models import UserDB, BookmarkDB
from jose import jwt,JWTError
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_TIME = 30

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_pass:str, hashed_pass:str):
    return pwd_context.verify(plain_pass,hashed_pass)

def create_access_token(data : dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)
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

Base.metadata.create_all(bind = engine)

class UserInp(BaseModel):
    username :str
    password : str

class BookmarkInp(BaseModel):
    url : str
    title : str

app = FastAPI()

@app.post('/users')
def signup(creds : UserInp, db:Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == creds.username).first()
    if user:
        raise HTTPException(status_code=401,detail="Username already exists")
    
    new_user = UserDB(
        username = creds.username,
        password = hash_password(creds.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message" : "new user created"
    }

@app.post('/login')
def login(creds : UserInp, db:Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == creds.username).first()
    if user is None or not verify_password(creds.password,user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub":user.username})

    return {
        "token" : token,
        "token_type" : "bearer"
    }

@app.post('/bookmarks')
def add_bookmark(bookmark : BookmarkInp, db:Session = Depends(get_db), current_user = Depends(get_current_user)):
    new_bookmark = BookmarkDB(
        url = bookmark.url,
        title = bookmark.title,
        owner_id = current_user.id
    )
    
    db.add(new_bookmark)
    db.commit()
    db.refresh(new_bookmark)

    return {
        "message" : "new bookmark added"
    }

@app.get('/bookmarks')
def get_bookmarks(db:Session = Depends(get_db), current_user = Depends(get_current_user)):
    bookmarks = db.query(BookmarkDB).filter(UserDB.username == current_user.username).all()
    return bookmarks
