from sqlalchemy import Column, Boolean, Integer, String
from database import Base

class NoteDB(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    owner_id = Column(Integer)

class UserDB(Base):

    __tablename__ = "credentials"
    id = Column(Integer,primary_key=True, index=True)
    username = Column(String)
    password = Column(String)