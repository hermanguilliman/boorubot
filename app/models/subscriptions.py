from sqlalchemy import Column, Integer, String

from app.models.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    tags = Column(String(255), unique=True)
