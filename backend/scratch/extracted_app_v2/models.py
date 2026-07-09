from sqlalchemy import Column, Integer, String, Text, Timestamp, ForeignKey
from sqlalchemy.orm import relationship
from db import Base
from typing import Optional


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(Timestamp, nullable=False, default='now')
    notes = relationship('Note', back_populates='author')


class Note(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(Timestamp, nullable=False, default='now')
    updated_at = Column(Timestamp, nullable=False, default='now')
    author = relationship('User', back_populates='notes')
