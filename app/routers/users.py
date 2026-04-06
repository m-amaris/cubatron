from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select
import os
import uuid
from typing import Optional
from app.database import get_session
from app.models import User, Dispense, DrinkRecipe
from app.dependencies import get_current_user
from app.security import hash_password
from pydantic import BaseModel


router = APIRouter()
AVATAR_DIR = "/opt/cubatron/app/static/avatars"
MAX_AVATAR_BYTES = 5 * 1024 * 1024
ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_THEME_MODES = {"dark", "light"}
ALLOWED_ACCENT_COLORS = {"emerald", "blue", "orange", "rose", "slate"}

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id, "username": user.username, "full_name": user.full_name,
        "role": user.role, "avatar_url": user.avatar_url, "favorite_mix": user.favorite_mix,
        "info": user.info,
        "xp": user.xp, "level": user.level,
        "theme_mode": user.theme_mode,
        "accent_color": user.accent_color,
        "created_at": user.created_at,
    }

@router.get("/me/drinks")
def get_my_drinks(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    dispenses = session.exec(
        select(Dispense)
        .where(Dispense.user_id == user.id)
        .order_by(Dispense.created_at.desc())
        .limit(5)
    ).all()

    recipe_ids = [d.recipe_id for d in dispenses]
    recipes_by_id: dict[int, DrinkRecipe] = {}
    if recipe_ids:
        recipes = session.exec(
            select(DrinkRecipe).where(DrinkRecipe.id.in_(recipe_ids))
        ).all()
        recipes_by_id = {r.id: r for r in recipes if r.id is not None}

    history = []
    for d in reversed(dispenses):
        recipe = recipes_by_id.get(d.recipe_id)
        history.append(
            {
                "name": recipe.name if recipe else f"Receta #{d.recipe_id}",
                "xp": d.xp_earned,
                "time": d.created_at.isoformat() if d.created_at else None,
            }
        )

    return history

@router.post("/me/update")
def update_profile(
    full_name: Optional[str] = Form(None),
    favorite_mix: Optional[str] = Form(None),
    info: Optional[str] = Form(None),
    theme_mode: Optional[str] = Form(None),
    accent_color: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if full_name: user.full_name = full_name
    if favorite_mix is not None:
        normalized_mix = favorite_mix.strip()
        if normalized_mix:
            recipes = session.exec(select(DrinkRecipe.name)).all()
            recipe_names = {name.lower().strip() for name in recipes if name}
            if normalized_mix.lower() not in recipe_names:
                raise HTTPException(status_code=400, detail="La bebida favorita debe ser una receta existente")
            user.favorite_mix = normalized_mix
        else:
            user.favorite_mix = None
    if info is not None:
        user.info = info.strip()[:140]
    if theme_mode is not None:
        normalized_theme = theme_mode.strip().lower()
        if normalized_theme not in ALLOWED_THEME_MODES:
            raise HTTPException(status_code=400, detail="Tema no permitido")
        user.theme_mode = normalized_theme
    if accent_color is not None:
        normalized_accent = accent_color.strip().lower()
        if normalized_accent not in ALLOWED_ACCENT_COLORS:
            raise HTTPException(status_code=400, detail="Acento no permitido")
        user.accent_color = normalized_accent
    
    if avatar:
        os.makedirs(AVATAR_DIR, exist_ok=True)

        original_name = avatar.filename or ""
        ext = os.path.splitext(original_name)[1].lower()
        if ext not in ALLOWED_AVATAR_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Formato de avatar no permitido")

        content_type = (avatar.content_type or "").lower()
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="El avatar debe ser una imagen")

        raw = avatar.file.read(MAX_AVATAR_BYTES + 1)
        if len(raw) > MAX_AVATAR_BYTES:
            raise HTTPException(status_code=400, detail="Avatar demasiado grande (max 5MB)")

        filename = f"{user.id}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(AVATAR_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(raw)
        user.avatar_url = f"/static/avatars/{filename}"

    session.add(user)
    session.commit()
    return {"message": "Perfil actualizado exitosamente", "avatar_url": user.avatar_url}

@router.get("/ranking")
def get_ranking(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    users = session.exec(select(User).order_by(User.xp.desc()).limit(10)).all()
    if not users:
        return []

    user_ids = [u.id for u in users if u.id is not None]
    dispenses = session.exec(select(Dispense).where(Dispense.user_id.in_(user_ids))).all()

    total_by_user: dict[int, int] = {uid: 0 for uid in user_ids}
    recipe_count_by_user: dict[int, dict[int, int]] = {uid: {} for uid in user_ids}
    recipe_ids: set[int] = set()

    for d in dispenses:
        uid = d.user_id
        total_by_user[uid] = total_by_user.get(uid, 0) + 1

        per_user = recipe_count_by_user.setdefault(uid, {})
        per_user[d.recipe_id] = per_user.get(d.recipe_id, 0) + 1
        recipe_ids.add(d.recipe_id)

    recipes_by_id: dict[int, str] = {}
    if recipe_ids:
        recipes = session.exec(select(DrinkRecipe).where(DrinkRecipe.id.in_(recipe_ids))).all()
        recipes_by_id = {r.id: r.name for r in recipes if r.id is not None}

    ranking = []
    for u in users:
        uid = u.id
        total = total_by_user.get(uid, 0)

        favorite_recipe_name = "-"
        per_user_recipe_count = recipe_count_by_user.get(uid, {})
        if per_user_recipe_count:
            favorite_recipe_id = max(
                per_user_recipe_count,
                key=lambda rid: per_user_recipe_count[rid],
            )
            favorite_recipe_name = recipes_by_id.get(favorite_recipe_id, f"Receta #{favorite_recipe_id}")

        ranking.append(
            {
                "username": u.username,
                "full_name": u.full_name,
                "level": u.level,
                "xp": u.xp,
                "avatar_url": u.avatar_url,
                "total_consumptions": total,
                "favorite_recipe_name": favorite_recipe_name,
            }
        )

    return ranking

class PasswordUpdate(BaseModel):
    new_password: str

@router.post("/me/password")
def update_password(data: PasswordUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    user.password_hash = hash_password(data.new_password)
    session.add(user)
    session.commit()
    return {"message": "Contraseña actualizada correctamente"}