from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select
import jwt
import os
import uuid
from typing import Optional
from app.database import get_session
from app.models import User, Dispense, MachineEvent
from app.config import SECRET_KEY, ALGORITHM
from pydantic import BaseModel


router = APIRouter()
AVATAR_DIR = "/opt/cubatron/app/static/avatars"

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
        "id": user.id, "username": user.username, "full_name": user.full_name,
        "role": user.role, "avatar_url": user.avatar_url, "favorite_mix": user.favorite_mix,
        "xp": user.xp, "level": user.level, "created_at": user.created_at,
    }

@router.get("/me/drinks")
def get_my_drinks(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    events = session.exec(select(MachineEvent).where(MachineEvent.event_type == "drink_made")).all()
    
    # Filtramos para quedarnos solo con las bebidas que hizo el usuario logueado
    my_events = [e for e in events if e.detail.startswith(user.username)]
    
    history = []
    for e in reversed(my_events[-5:]): # Cogemos las últimas 5
        drink_name = e.detail.split(" preparó ")[-1]
        history.append({"name": drink_name})
        
    return history

@router.post("/me/update")
def update_profile(
    full_name: Optional[str] = Form(None),
    favorite_mix: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if full_name: user.full_name = full_name
    if favorite_mix: user.favorite_mix = favorite_mix
    
    if avatar:
        os.makedirs(AVATAR_DIR, exist_ok=True)
        ext = avatar.filename.split(".")[-1]
        filename = f"{user.id}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(AVATAR_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(avatar.file.read())
        user.avatar_url = f"/static/avatars/{filename}"

    session.add(user)
    session.commit()
    return {"message": "Perfil actualizado exitosamente", "avatar_url": user.avatar_url}

@router.get("/ranking")
def get_ranking(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    # Devuelve el top 10 usuarios ordenados por XP
    users = session.exec(select(User).order_by(User.xp.desc()).limit(10)).all()
    return [{"username": u.username, "full_name": u.full_name, "level": u.level, "xp": u.xp, "avatar_url": u.avatar_url} for u in users]

class PasswordUpdate(BaseModel):
    new_password: str

@router.post("/me/password")
def update_password(data: PasswordUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    from app.security import get_password_hash
    user.password_hash = get_password_hash(data.new_password)
    session.add(user)
    session.commit()
    return {"message": "Contraseña actualizada correctamente"}