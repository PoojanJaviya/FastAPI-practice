from sqlalchemy import Column, Boolean, Integer, String
from database import Base

class ToDoDB(Base):
    __tablename__ = "to_do_list"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    priority = Column(Integer)
    status = Column(Boolean)

class UserDB(Base):

    __tablename__ = "credentials"

    username = Column(String, primary_key=True)
    password = Column(String)