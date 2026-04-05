from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import engine
from app.models import User
from app.security import verify_password, create_access_token

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginRequest):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == data.username)).first()
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        token = create_access_token({
            "sub": user.username,
            "role": user.role,
            "user_id": user.id
        })
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": user.username,
            "role": user.role
        }
