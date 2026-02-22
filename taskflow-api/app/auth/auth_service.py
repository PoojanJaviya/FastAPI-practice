from sqlalchemy.orm import Session
from app.models.user_model import User
from app.auth.auth_schema import UserSignup, UserLogin
from app.auth.utils import hash_password, verify_password
from app.auth.utils import create_access_token

def create_user(db: Session, user_data: UserSignup):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        return None

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, user_data: UserLogin):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        return None

    if not verify_password(user_data.password, user.hashed_password):
        return None

    return user

def login_user(db: Session, user_data: UserLogin):
    user = authenticate_user(db, user_data)
    if not user:
        return None

    access_token = create_access_token({"sub": user.email})
    return access_token