from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlmodel import Session, select
import os
import uuid
from datetime import timezone
from typing import Optional
from app.database import get_session
from app.models import User, Dispense, DrinkRecipe
from app.dependencies import get_current_user
from app.security import hash_password
from app.security import verify_password, create_access_token
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
    data = get_history(
        scope="me",
        page=1,
        page_size=5,
        q="",
        session=session,
        user=user,
    )
    return data["items"]


@router.get("/history")
def get_history(
    scope: str = Query(default="all", pattern="^(all|me)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    q: str = Query(default="", max_length=80),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    base_query = select(Dispense).order_by(Dispense.created_at.desc())
    if scope == "me":
        base_query = base_query.where(Dispense.user_id == user.id)

    dispenses = session.exec(base_query).all()
    if not dispenses:
        return {
            "items": [],
            "page": page,
            "page_size": page_size,
            "total": 0,
            "total_pages": 0,
        }

    recipe_ids = list({d.recipe_id for d in dispenses})
    user_ids = list({d.user_id for d in dispenses})

    recipes = session.exec(select(DrinkRecipe).where(DrinkRecipe.id.in_(recipe_ids))).all() if recipe_ids else []
    users = session.exec(select(User).where(User.id.in_(user_ids))).all() if user_ids else []

    recipe_name_by_id = {r.id: r.name for r in recipes if r.id is not None}
    user_by_id = {u.id: u for u in users if u.id is not None}

    rows = []
    for d in dispenses:
        owner = user_by_id.get(d.user_id)
        recipe_name = recipe_name_by_id.get(d.recipe_id, f"Receta #{d.recipe_id}")
        rows.append(
            {
                "name": recipe_name,
                "xp": d.xp_earned,
                "time": d.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if d.created_at else None,
                "username": owner.username if owner else f"user-{d.user_id}",
                "full_name": owner.full_name if owner else f"Usuario #{d.user_id}",
                "avatar_url": owner.avatar_url if owner else None,
                "glass_type": d.glass_type,
                "serving_mode": d.serving_mode,
            }
        )

    needle = (q or "").strip().lower()
    if needle:
        rows = [
            row
            for row in rows
            if needle in (row.get("name") or "").lower()
            or needle in (row.get("username") or "").lower()
            or needle in (row.get("full_name") or "").lower()
            or needle in (row.get("glass_type") or "").lower()
            or needle in (row.get("serving_mode") or "").lower()
        ]

    total = len(rows)
    total_pages = (total + page_size - 1) // page_size if total else 0
    safe_page = min(page, total_pages) if total_pages else 1
    start = (safe_page - 1) * page_size
    end = start + page_size

    return {
        "items": rows[start:end],
        "page": safe_page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }

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

        most_consumed_recipe_name = "-"
        per_user_recipe_count = recipe_count_by_user.get(uid, {})
        if per_user_recipe_count:
            most_consumed_recipe_id = max(
                per_user_recipe_count,
                key=lambda rid: per_user_recipe_count[rid],
            )
            most_consumed_recipe_name = recipes_by_id.get(most_consumed_recipe_id, f"Receta #{most_consumed_recipe_id}")

        ranking.append(
            {
                "username": u.username,
                "full_name": u.full_name,
                "level": u.level,
                "xp": u.xp,
                "avatar_url": u.avatar_url,
                "total_consumptions": total,
                "most_consumed_recipe_name": most_consumed_recipe_name,
                "favorite_recipe_name": most_consumed_recipe_name,
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


class PinUpdate(BaseModel):
    pin: str


@router.post("/me/pin")
def update_pin(data: PinUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    pin = (data.pin or "").strip()
    if not pin or not pin.isdigit() or len(pin) != 6:
        raise HTTPException(status_code=400, detail="El PIN debe tener exactamente 6 dígitos")
    user.pin_hash = hash_password(pin)
    session.add(user)
    session.commit()
    return {"message": "PIN configurado correctamente"}


class PinLoginRequest(BaseModel):
    user_id: int
    pin: str


@router.post("/touch/pin-login")
def touch_pin_login(data: PinLoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.id == data.user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not getattr(user, "pin_hash", None):
        raise HTTPException(status_code=403, detail="PIN no configurado para este usuario")
    pin = (data.pin or "").strip()
    if not pin or not pin.isdigit() or len(pin) != 6:
        raise HTTPException(status_code=400, detail="PIN inválido")
    if not verify_password(pin, user.pin_hash):
        raise HTTPException(status_code=401, detail="PIN inválido")

    token = create_access_token({"sub": user.username, "role": user.role, "user_id": user.id}, expires_minutes=60)
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "user_id": user.id,
        "full_name": user.full_name,
        "role": user.role,
    }


@router.get("/touch/list")
def touch_user_list(session: Session = Depends(get_session)):
    users = session.exec(select(User).where(User.is_archived == False)).all()
    out = []
    for u in users:
        out.append({
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "avatar_url": u.avatar_url,
        })
    return out