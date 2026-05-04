from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.config import get_db
from app.models.models import User
from app.services.auth_service import verify_password, create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post('/login')
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = create_access_token({"sub": user.username, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}
