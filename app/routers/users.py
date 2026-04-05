from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select
import jwt
from app.database import get_session
from app.models import User, Dispense
from app.config import SECRET_KEY, ALGORITHM

router = APIRouter()

def get_current_user(authorization: str = Header(None), session: Session = Depends(get_session)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = session.exec(select(User).where(User.id == payload["user_id"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "avatar_url": user.avatar_url,
        "favorite_mix": user.favorite_mix,
        "xp": user.xp,
        "level": user.level,
        "created_at": user.created_at,
    }

@router.get("/me/drinks")
def my_drinks(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    drinks = session.exec(
        select(Dispense).where(Dispense.user_id == user.id).order_by(Dispense.created_at.desc())
    ).all()
    return drinks[:10]
