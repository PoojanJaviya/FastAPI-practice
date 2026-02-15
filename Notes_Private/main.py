# from fastapi import FastAPI, Depends, HTTPException
# from pydantic import BaseModel, Field
# from sqlalchemy.orm import Session
# from jose import jwt,JWTError
# from passlib.context import CryptContext
# from datetime import datetime, timedelta
# from fastapi.security import OAuth2PasswordBearer
# from database import SessionLocal
# from models import UserDB, NoteDB, Base
# from database import engine


# SECRET_KEY = "key"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30
# ALGORITHM = 'HS256'
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# pwd_context = CryptContext(schemes=['bcrypt'],deprecated="auto")
# def hash_password(password : str):
#     return pwd_context.hash(password)

# def verify(password : str, hashed_password : str):
#     return pwd_context.verify(password,hashed_password)

# def create_access_token(data : dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({'exp':expire})
#     return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

# def get_current_user(
#         token :str =  Depends(oauth2_scheme),
#         db : Session = Depends(get_db)
# ):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401)
#     except JWTError:
#         raise HTTPException(status_code=401)
    
#     user = db.query(UserDB).filter(username == UserDB.username).first()
#     if user is None:
#         raise HTTPException(status_code=401)
    
#     return user

# class Credential(BaseModel):
#     username :str
#     password : str

# class Notes(BaseModel):
#     content : str

# app = FastAPI()
# Base.metadata.create_all(bind=engine)

# @app.post('/users')
# def sign_up(details : Credential,db : Session = Depends(get_db)):
#     user = db.query(UserDB).filter(UserDB.username == details.username).first()

#     if user:
#         return {"message" : "user already exists"}
    
#     new_user = UserDB(
#         username = details.username,
#         password = hash_password(details.password)
#     )

#     db.add(new_user)
#     db.commit()

#     return {"message" : "new user created"}


# @app.post('/login')
# def login(creds : Credential, db : Session = Depends(get_db)):
#     user = db.query(UserDB).filter(UserDB.username==creds.username).first()

#     if user is None:
#         raise HTTPException(status_code=404,detail= "user not found")
#     if not verify(creds.password,user.password):
#         raise HTTPException(status_code=401, detail="Invalid Credentials")

#     token = create_access_token({"sub" : user.username})

#     return {
#         "access_token" : token,
#         "token_type" : "bearer"
#     }

# @app.post('/notes')
# def add_notes(inp : Notes, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

#     new_note = NoteDB(
#         content = inp.content,
#         owner_id = current_user.id
#     )

#     db.add(new_note)
#     db.commit()

#     return {"message" : "new note added",
#             "note" : new_note}

# @app.get('/notes')
# def get_notes(db: Session = Depends(get_db), current_user = Depends(get_current_user)):

#     notes = db.query(NoteDB).filter(NoteDB.owner_id == current_user.id).all()
    
#     return {
#         "notes" : notes[0].content
#     }


from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta

from database import SessionLocal, engine
from models import UserDB, NoteDB, Base


# =======================
# APP & DATABASE SETUP
# =======================

app = FastAPI()
Base.metadata.create_all(bind=engine)


# =======================
# JWT CONFIG
# =======================

SECRET_KEY = "key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# =======================
# PASSWORD UTILS
# =======================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password[:72], hashed_password)


# =======================
# DATABASE DEPENDENCY
# =======================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =======================
# JWT UTILS
# =======================

def create_access_token(data: dict) -> str:
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
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user


# =======================
# SCHEMAS
# =======================

class Credential(BaseModel):
    username: str
    password: str = Field(min_length=4)


class NoteCreate(BaseModel):
    content: str


# =======================
# AUTH ENDPOINTS
# =======================

@app.post("/users", status_code=status.HTTP_201_CREATED)
def sign_up(details: Credential, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(
        UserDB.username == details.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )

    new_user = UserDB(
        username=details.username,
        password=hash_password(details.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}


@app.post("/login")
def login(creds: Credential, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(
        UserDB.username == creds.username
    ).first()

    if not user or not verify_password(creds.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token({"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# =======================
# NOTES ENDPOINTS (PROTECTED)
# =======================

@app.post("/notes", status_code=status.HTTP_201_CREATED)
def add_note(
    inp: NoteCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    new_note = NoteDB(
        content=inp.content,
        owner_id=current_user.id
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return {
        "message": "Note created",
        "note": new_note
    }


@app.get("/notes")
def get_notes(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    notes = db.query(NoteDB).filter(
        NoteDB.owner_id == current_user.id
    ).all()

    return notes
