from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.config import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    gender = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Ingredient(Base):
    __tablename__ = 'ingredients'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)


class Deposit(Base):
    __tablename__ = 'deposits'
    id = Column(Integer, primary_key=True, index=True)
    slot = Column(Integer, nullable=False)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), nullable=True)
    level_ml = Column(Integer, default=1000)
    capacity_ml = Column(Integer, default=1000)
    ingredient = relationship('Ingredient')


class Recipe(Base):
    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    # composition: mapping slot->percent (sum 100)
    composition = Column(JSON, nullable=False, default={})


class Cup(Base):
    __tablename__ = 'cups'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    capacity_ml = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)


class History(Base):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=True)
    cup_id = Column(Integer, ForeignKey('cups.id'), nullable=True)
    ml_total = Column(Integer, default=0)
    mode = Column(String, nullable=True)
    xp_gained = Column(Integer, default=0)
    success = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
