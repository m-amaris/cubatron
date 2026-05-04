from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.config import get_db
from app.models.models import User
from app.models.schemas import UserUpdate
from app.services.auth_service import decode_access_token, get_password_hash

router = APIRouter()


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail='Not authenticated')
    scheme, _, token = authorization.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        raise HTTPException(status_code=401, detail='Invalid auth header')
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid token')
    username = payload.get('sub')
    if not username:
        raise HTTPException(status_code=401, detail='Invalid token')
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail='Admin access required')
    return current_user


@router.post('/', summary='Create user')
def create_user(payload: dict, db: Session = Depends(get_db)):
    username = payload.get('username')
    password = payload.get('password')
    if not username or not password:
        raise HTTPException(status_code=400, detail='username and password required')
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail='username exists')
    user = User(username=username, hashed_password=get_password_hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username}


@router.get('/', summary='List users')
def list_users(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        {"id": u.id, "username": u.username, "is_admin": u.is_admin, "xp": u.xp, "gender": u.gender}
        for u in users
    ]


@router.get('/me')
def read_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "is_admin": current_user.is_admin, "xp": current_user.xp, "gender": current_user.gender}


@router.patch('/me', summary='Update user profile')
def update_me(payload: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.username is not None:
        if db.query(User).filter(User.username == payload.username, User.id != current_user.id).first():
            raise HTTPException(status_code=400, detail='Username already taken')
        current_user.username = payload.username
    if payload.gender is not None:
        current_user.gender = payload.gender
    db.commit()
    db.refresh(current_user)
    return {"id": current_user.id, "username": current_user.username, "is_admin": current_user.is_admin, "xp": current_user.xp, "gender": current_user.gender}


@router.patch('/{user_id}', summary='Update any user')
def update_user(user_id: int, payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail='User not found')
    if target.id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail='Admin access required')
    if payload.get('username') is not None:
        if db.query(User).filter(User.username == payload.get('username'), User.id != target.id).first():
            raise HTTPException(status_code=400, detail='Username already taken')
        target.username = payload.get('username')
    if payload.get('gender') is not None:
        target.gender = payload.get('gender')
    if payload.get('is_admin') is not None:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail='Admin access required')
        target.is_admin = bool(payload.get('is_admin'))
    db.commit()
    db.refresh(target)
    return {"id": target.id, "username": target.username, "is_admin": target.is_admin, "xp": target.xp, "gender": target.gender}


@router.delete('/{user_id}', summary='Delete user')
def delete_user(user_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail='User not found')
    if target.id == admin_user.id:
        raise HTTPException(status_code=400, detail='Cannot delete yourself')
    db.delete(target)
    db.commit()
    return {"status": "deleted", "id": user_id}


@router.get('/ranking')
def ranking(limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.xp.desc()).limit(limit).all()
    return [{"id": u.id, "username": u.username, "xp": u.xp} for u in users]
