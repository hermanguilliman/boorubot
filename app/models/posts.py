from sqlalchemy import Column, Integer

from app.models.base import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
