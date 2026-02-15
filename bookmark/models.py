from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class BookmarkDB(Base):
    __tablename__ = "bookmarks"

    bookmark_id = Column(Integer,primary_key=True,index=True)
    url = Column(String)
    title = Column(String)

    owner_id = Column(Integer, ForeignKey("users.id"))

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer,index=True, primary_key=True)
    username = Column(Integer, unique=True)
    password = Column(String)
    