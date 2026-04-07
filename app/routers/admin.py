from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, constr
from sqlmodel import Session, select
from typing import Optional
import json
import re
from app.database import get_session
from app.models import User, Tank, DrinkRecipe, MachineEvent, GlassType
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
    username: constr(min_length=3, max_length=32)
    password: constr(min_length=8, max_length=128)
    full_name: constr(min_length=1, max_length=80)
    role: constr(pattern="^(user|admin)$")


class LiquidSetting(BaseModel):
    name: constr(min_length=1, max_length=40)
    type: constr(pattern="^(mixer|alcohol)$")


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
    key: Optional[constr(min_length=1, max_length=32, pattern=r"^[a-z0-9_-]+$")] = None
    name: constr(min_length=1, max_length=40)
    icon: constr(min_length=1, max_length=8) = "🥤"
    capacity_ml: int = Field(ge=30, le=2000)
    enabled: bool = True


class GlassUpdate(BaseModel):
    name: constr(min_length=1, max_length=40)
    icon: constr(min_length=1, max_length=8) = "🥤"
    capacity_ml: int = Field(ge=30, le=2000)
    enabled: bool = True


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
    return {
        "users": len(session.exec(select(User)).all()),
        "recipes": len(session.exec(select(DrinkRecipe)).all()),
        "tanks": len(session.exec(select(Tank)).all()),
        "events": len(session.exec(select(MachineEvent)).all())
    }

@router.get("/settings")
def get_settings(admin: User = Depends(require_admin)):
    return SYSTEM_SETTINGS

@router.post("/settings")
def update_settings(settings: AdminSettingsUpdate, admin: User = Depends(require_admin)):
    global SYSTEM_SETTINGS
    SYSTEM_SETTINGS.update(settings.model_dump())
    return SYSTEM_SETTINGS

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
        password_hash=hash_password(user_data.password)
    )
    session.add(new_user)
    session.commit()
    return {"message": "Usuario creado"}

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