from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from typing import Optional, Annotated
from datetime import datetime
import json
import re
from app.database import get_session
from app.models import User, Tank, DrinkRecipe, MachineEvent, GlassType, Dispense
from app.security import hash_password
from app.dependencies import require_admin

router = APIRouter()

# Guardamos la configuración de polling en memoria para la V1
SYSTEM_SETTINGS = {
    "poll_status": 3000,
    "poll_tanks": 10000,
    "poll_history": 30000,
    "liquids": [
        {"name": "CocaCola", "type": "mixer"},
        {"name": "Limón", "type": "mixer"},
        {"name": "Ron", "type": "alcohol"},
        {"name": "Ginebra", "type": "alcohol"}
    ]
}

class UserCreate(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=32)]
    password: Annotated[str, Field(min_length=8, max_length=128)]
    full_name: Annotated[str, Field(min_length=1, max_length=80)]
    role: Annotated[str, Field(pattern="^(user|admin)$")]
    xp: Annotated[int, Field(default=0, ge=0, le=999999)] = 0
    level: Annotated[int, Field(default=1, ge=1, le=999)] = 1
    favorite_mix: Annotated[Optional[str], Field(default=None, max_length=80)] = None
    info: Annotated[str, Field(default="", max_length=140)] = ""
    theme_mode: Annotated[str, Field(default="dark", pattern="^(dark|light)$")] = "dark"
    accent_color: Annotated[str, Field(default="emerald", pattern="^(emerald|blue|orange|rose|slate)$")] = "emerald"
    avatar_url: Annotated[Optional[str], Field(default=None, max_length=255)] = None


class UserUpdate(BaseModel):
    username: Annotated[Optional[str], Field(default=None, min_length=3, max_length=32)] = None
    full_name: Annotated[Optional[str], Field(default=None, min_length=1, max_length=80)] = None
    password: Annotated[Optional[str], Field(default=None, min_length=8, max_length=128)] = None
    role: Annotated[Optional[str], Field(default=None, pattern="^(user|admin)$")] = None
    xp: Annotated[Optional[int], Field(default=None, ge=0, le=999999)] = None
    level: Annotated[Optional[int], Field(default=None, ge=1, le=999)] = None
    favorite_mix: Annotated[Optional[str], Field(default=None, max_length=80)] = None
    info: Annotated[Optional[str], Field(default=None, max_length=140)] = None
    theme_mode: Annotated[Optional[str], Field(default=None, pattern="^(dark|light)$")] = None
    accent_color: Annotated[Optional[str], Field(default=None, pattern="^(emerald|blue|orange|rose|slate)$")] = None
    avatar_url: Annotated[Optional[str], Field(default=None, max_length=255)] = None


class UserArchiveUpdate(BaseModel):
    is_archived: bool = True


class LiquidSetting(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=40)]
    type: Annotated[str, Field(pattern="^(mixer|alcohol)$")]


class LiquidUpdate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=40)]
    type: Annotated[str, Field(pattern="^(mixer|alcohol)$")]


class AdminSettingsUpdate(BaseModel):
    poll_status: int = Field(default=3000, ge=500, le=120000)
    poll_tanks: int = Field(default=10000, ge=500, le=120000)
    poll_history: int = Field(default=30000, ge=500, le=120000)
    liquids: list[LiquidSetting] = Field(default_factory=list)

class RecipeCreate(BaseModel):
    name: str
    description: str
    ingredients: str
    xp_reward: int
    glass_options: list[str] = Field(default_factory=lambda: ["highball", "rocks"])
    serving_modes: dict[str, dict[str, float]] = Field(default_factory=dict)
    
class RecipeUpdate(BaseModel):
    name: str
    description: str
    ingredients: str  # Ej: "Ron, Cola"
    xp_reward: int
    glass_options: list[str] = Field(default_factory=lambda: ["highball", "rocks"])
    serving_modes: dict[str, dict[str, float]] = Field(default_factory=dict)


class GlassCreate(BaseModel):
    key: Annotated[Optional[str], Field(default=None, min_length=1, max_length=32, pattern=r"^[a-z0-9_-]+$")] = None
    name: Annotated[str, Field(min_length=1, max_length=40)]
    icon: Annotated[str, Field(min_length=1, max_length=8)] = "🥤"
    capacity_ml: Annotated[int, Field(ge=30, le=2000)]
    enabled: bool = True


class GlassUpdate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=40)]
    icon: Annotated[str, Field(min_length=1, max_length=8)] = "🥤"
    capacity_ml: Annotated[int, Field(ge=30, le=2000)]
    enabled: bool = True


def _user_out(user: User, consumptions: int = 0, last_activity: Optional[str] = None) -> dict:
    out = user.model_dump() if hasattr(user, "model_dump") else user.dict()
    out["consumptions"] = consumptions
    out["last_activity"] = last_activity
    out["created_at"] = user.created_at.isoformat() if getattr(user, "created_at", None) else None
    out["archived_at"] = user.archived_at.isoformat() if getattr(user, "archived_at", None) else None
    return out


def _slugify_glass_key(value: str) -> str:
    normalized = (value or "").strip().lower()
    normalized = re.sub(r"[^a-z0-9_-]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized[:32] or "glass"


def _safe_load_json(value: str, fallback):
    try:
        loaded = json.loads(value or "")
        return loaded if loaded is not None else fallback
    except Exception:
        return fallback


def _recipe_out(recipe: DrinkRecipe) -> dict:
    out = recipe.model_dump() if hasattr(recipe, "model_dump") else recipe.dict()
    out["glass_options"] = _safe_load_json(getattr(recipe, "glass_options_json", "[]"), [])
    out["serving_modes"] = _safe_load_json(getattr(recipe, "serving_modes_json", "{}"), {})
    return out


def _glass_out(glass: GlassType) -> dict:
    out = glass.model_dump() if hasattr(glass, "model_dump") else glass.dict()
    out["capacity_ml"] = int(out.get("capacity_ml", 300))
    return out

@router.get("/overview")
def overview(session: Session = Depends(get_session), admin: User = Depends(require_admin)):
    users = session.exec(select(User)).all()
    recipes = session.exec(select(DrinkRecipe)).all()
    glasses = session.exec(select(GlassType)).all()
    tanks = session.exec(select(Tank)).all()
    events = session.exec(select(MachineEvent)).all()
    return {
        "users": len(users),
        "admins": sum(1 for user in users if user.role == "admin"),
        "recipes": len(recipes),
        "enabled_recipes": sum(1 for recipe in recipes if getattr(recipe, "enabled", True)),
        "glasses": len(glasses),
        "enabled_glasses": sum(1 for glass in glasses if getattr(glass, "enabled", True)),
        "liquids": len(SYSTEM_SETTINGS.get("liquids", [])),
        "tanks": len(tanks),
        "events": len(events),
    }


@router.get("/users")
def list_users(session: Session = Depends(get_session), admin: User = Depends(require_admin)):
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
    dispenses = session.exec(select(Dispense).order_by(Dispense.created_at.desc())).all()

    consumptions_by_user: dict[int, int] = {}
    last_activity_by_user: dict[int, str] = {}

    for dispense in dispenses:
        consumptions_by_user[dispense.user_id] = consumptions_by_user.get(dispense.user_id, 0) + 1
        if dispense.user_id not in last_activity_by_user and dispense.created_at:
            last_activity_by_user[dispense.user_id] = dispense.created_at.isoformat()

    return [
        _user_out(
            user,
            consumptions=consumptions_by_user.get(user.id or -1, 0),
            last_activity=last_activity_by_user.get(user.id or -1),
        )
        for user in users
    ]


@router.get("/users/{user_id}/activity")
def get_user_activity(
    user_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    dispenses = session.exec(
        select(Dispense).where(Dispense.user_id == user_id).order_by(Dispense.created_at.desc()).limit(12)
    ).all()

    recipe_ids = list({d.recipe_id for d in dispenses})
    recipe_names = {}
    if recipe_ids:
        recipes = session.exec(select(DrinkRecipe).where(DrinkRecipe.id.in_(recipe_ids))).all()
        recipe_names = {recipe.id: recipe.name for recipe in recipes if recipe.id is not None}

    return {
        "user": _user_out(user),
        "items": [
            {
                "type": d.action or "make_drink",
                "status": d.status,
                "recipe": recipe_names.get(d.recipe_id, f"Receta #{d.recipe_id}"),
                "xp": d.xp_earned,
                "glass_type": d.glass_type,
                "serving_mode": d.serving_mode,
                "time": d.created_at.isoformat() if d.created_at else None,
            }
            for d in dispenses
        ],
    }

@router.get("/settings")
def get_settings(admin: User = Depends(require_admin)):
    return SYSTEM_SETTINGS

@router.post("/settings")
def update_settings(settings: AdminSettingsUpdate, admin: User = Depends(require_admin)):
    global SYSTEM_SETTINGS
    SYSTEM_SETTINGS.update(settings.model_dump())
    return SYSTEM_SETTINGS


@router.post("/settings/liquids/{liquid_index}")
def update_liquid(
    liquid_index: int,
    data: LiquidUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    liquids = SYSTEM_SETTINGS.get("liquids", [])
    if liquid_index < 0 or liquid_index >= len(liquids):
        raise HTTPException(status_code=404, detail="Líquido no encontrado")

    previous = liquids[liquid_index]
    old_name = str(previous.get("name", ""))
    liquids[liquid_index] = data.model_dump()
    SYSTEM_SETTINGS["liquids"] = liquids

    if old_name and old_name.lower() != data.name.lower():
        recipes = session.exec(select(DrinkRecipe)).all()
        for recipe in recipes:
            ingredients = [item.strip() for item in (recipe.ingredients or "").split(",") if item.strip()]
            updated = [data.name if item.lower() == old_name.lower() else item for item in ingredients]
            if updated != ingredients:
                recipe.ingredients = ", ".join(updated)
                session.add(recipe)

        tanks = session.exec(select(Tank)).all()
        for tank in tanks:
            if (tank.name or "").lower() == old_name.lower():
                tank.name = data.name
            if (tank.content or "").lower() == old_name.lower():
                tank.content = data.name
            session.add(tank)

        session.commit()

    return {"message": "Líquido actualizado", "settings": SYSTEM_SETTINGS, "renamed_from": old_name}

@router.post("/users/create")
def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    existing = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    new_user = User(
        username=user_data.username,
        full_name=user_data.full_name,
        role=user_data.role,
        password_hash=hash_password(user_data.password),
        xp=user_data.xp,
        level=user_data.level,
        favorite_mix=user_data.favorite_mix.strip() if user_data.favorite_mix else None,
        info=user_data.info.strip()[:140],
        theme_mode=user_data.theme_mode,
        accent_color=user_data.accent_color,
        avatar_url=user_data.avatar_url.strip() if user_data.avatar_url else None,
    )

    if new_user.favorite_mix:
        recipe_names = {name.lower().strip() for name in session.exec(select(DrinkRecipe.name)).all() if name}
        if new_user.favorite_mix.lower() not in recipe_names:
            raise HTTPException(status_code=400, detail="La bebida favorita debe ser una receta existente")

    session.add(new_user)
    session.commit()
    return {"message": "Usuario creado"}


@router.post("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.username is not None:
        normalized_username = data.username.strip()
        if normalized_username != user.username:
            existing = session.exec(select(User).where(User.username == normalized_username, User.id != user_id)).first()
            if existing:
                raise HTTPException(status_code=400, detail="El usuario ya existe")
            user.username = normalized_username

    if data.full_name is not None:
        user.full_name = data.full_name.strip() or user.full_name

    if data.password:
        user.password_hash = hash_password(data.password)

    if data.role is not None:
        user.role = data.role

    if data.xp is not None:
        user.xp = data.xp

    if data.level is not None:
        user.level = data.level

    if data.favorite_mix is not None:
        favorite_mix = data.favorite_mix.strip()
        if favorite_mix:
            recipe_names = {name.lower().strip() for name in session.exec(select(DrinkRecipe.name)).all() if name}
            if favorite_mix.lower() not in recipe_names:
                raise HTTPException(status_code=400, detail="La bebida favorita debe ser una receta existente")
            user.favorite_mix = favorite_mix
        else:
            user.favorite_mix = None

    if data.info is not None:
        user.info = data.info.strip()[:140]

    if data.theme_mode is not None:
        user.theme_mode = data.theme_mode

    if data.accent_color is not None:
        user.accent_color = data.accent_color

    if data.avatar_url is not None:
        avatar_url = data.avatar_url.strip()
        user.avatar_url = avatar_url or None

    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "Usuario actualizado", "user": _user_out(user)}


@router.post("/users/{user_id}/archive")
def archive_user(
    user_id: int,
    data: UserArchiveUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="No puedes archivarte a ti mismo")

    user.is_archived = data.is_archived
    user.archived_at = datetime.utcnow() if data.is_archived else None
    user.archived_by = admin.username if data.is_archived else None
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "Usuario archivado" if data.is_archived else "Usuario restaurado", "user": _user_out(user)}


@router.delete("/users/{user_id}")
def purge_user(
    user_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    if not getattr(user, "is_archived", False):
        raise HTTPException(status_code=400, detail="Archiva el usuario antes de eliminarlo de forma segura")

    has_dispenses = session.exec(select(Dispense).where(Dispense.user_id == user_id).limit(1)).first()
    if has_dispenses:
        raise HTTPException(status_code=400, detail="No se puede eliminar un usuario con historial de consumiciones")

    session.delete(user)
    session.commit()
    return {"message": "Usuario eliminado de forma segura"}

@router.get("/recipes")
def get_admin_recipes(session: Session = Depends(get_session), admin: User = Depends(require_admin)):
    recipes = session.exec(select(DrinkRecipe)).all()
    return [_recipe_out(r) for r in recipes]

@router.post("/recipes/create")
def create_recipe(
    data: RecipeCreate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    recipe = DrinkRecipe(
        name=data.name,
        description=data.description,
        ingredients=data.ingredients,
        xp_reward=data.xp_reward,
        glass_options_json=json.dumps(data.glass_options, ensure_ascii=True),
        serving_modes_json=json.dumps(data.serving_modes, ensure_ascii=True),
    )
    session.add(recipe)
    session.commit()
    return {"message": "Receta creada"}


@router.post("/recipes/{recipe_id}")
def update_recipe(
    recipe_id: int,
    data: RecipeUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == recipe_id)).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    recipe.name = data.name
    recipe.description = data.description
    recipe.ingredients = data.ingredients
    recipe.xp_reward = data.xp_reward
    recipe.glass_options_json = json.dumps(data.glass_options, ensure_ascii=True)
    recipe.serving_modes_json = json.dumps(data.serving_modes, ensure_ascii=True)
    
    session.add(recipe)
    session.commit()
    return {"message": "Receta actualizada", "recipe": _recipe_out(recipe)}



@router.delete("/recipes/{recipe_id}")
def delete_recipe(
    recipe_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == recipe_id)).first()
    if recipe:
        session.delete(recipe)
        session.commit()
    return {"message": "Receta eliminada"}


@router.get("/glasses")
def get_glasses(session: Session = Depends(get_session), admin: User = Depends(require_admin)):
    glasses = session.exec(select(GlassType).order_by(GlassType.name.asc())).all()
    return [_glass_out(g) for g in glasses]


@router.post("/glasses/create")
def create_glass(
    data: GlassCreate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    key = data.key or _slugify_glass_key(data.name)
    exists = session.exec(select(GlassType).where(GlassType.key == key)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Ya existe un vaso con esa clave")
    glass = GlassType(
        key=key,
        name=data.name,
        icon=data.icon,
        capacity_ml=data.capacity_ml,
        enabled=data.enabled,
    )
    session.add(glass)
    session.commit()
    session.refresh(glass)
    return {"message": "Vaso creado", "glass": _glass_out(glass)}


@router.post("/glasses/{glass_id}")
def update_glass(
    glass_id: int,
    data: GlassUpdate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    glass = session.exec(select(GlassType).where(GlassType.id == glass_id)).first()
    if not glass:
        raise HTTPException(status_code=404, detail="Vaso no encontrado")

    glass.name = data.name
    glass.icon = data.icon
    glass.capacity_ml = data.capacity_ml
    glass.enabled = data.enabled
    session.add(glass)
    session.commit()
    session.refresh(glass)
    return {"message": "Vaso actualizado", "glass": _glass_out(glass)}


@router.delete("/glasses/{glass_id}")
def delete_glass(
    glass_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    glass = session.exec(select(GlassType).where(GlassType.id == glass_id)).first()
    if not glass:
        raise HTTPException(status_code=404, detail="Vaso no encontrado")

    for recipe in session.exec(select(DrinkRecipe)).all():
        options = _safe_load_json(getattr(recipe, "glass_options_json", "[]"), [])
        if not isinstance(options, list) or glass.key not in options:
            continue
        recipe.glass_options_json = json.dumps([key for key in options if key != glass.key], ensure_ascii=True)
        session.add(recipe)

    session.delete(glass)
    session.commit()
    return {"message": "Vaso eliminado"}