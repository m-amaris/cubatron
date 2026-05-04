from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class UserUpdate(BaseModel):
    username: Optional[str]
    gender: Optional[str]


class UserRead(BaseModel):
    id: int
    username: str
    is_admin: bool
    xp: int
    gender: Optional[str]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class RecipeRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    composition: Dict[str, Any]

    class Config:
        orm_mode = True


class CupRead(BaseModel):
    id: int
    name: str
    capacity_ml: int

    class Config:
        orm_mode = True


class HistoryRead(BaseModel):
    id: int
    user_id: Optional[int]
    recipe_id: Optional[int]
    cup_id: Optional[int]
    ml_total: int
    mode: Optional[str]
    xp_gained: int
    success: bool
    created_at: datetime

    class Config:
        orm_mode = True
