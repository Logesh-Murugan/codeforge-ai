from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db import Base
from typing import Optional

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default='now')
    notes = relationship('Note', back_populates='author')


class Note(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default='now')
    updated_at = Column(DateTime, nullable=False, default='now', onupdate='now')
    author = relationship('User', back_populates='notes')
