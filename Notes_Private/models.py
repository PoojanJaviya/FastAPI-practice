from sqlalchemy import Column, Boolean, Integer, String, ForeignKey
from database import Base

class NoteDB(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    owner_id = Column(Integer, ForeignKey('credentials.id'))

class UserDB(Base):

    __tablename__ = "credentials"
    id = Column(Integer,primary_key=True, index=True)
    username = Column(String)
    password = Column(String)