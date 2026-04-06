from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
import json
from app.database import get_session
from app.models import User, DrinkRecipe, Dispense, MachineEvent
from app.schemas import MakeDrinkRequest
from app.dependencies import get_current_user

router = APIRouter()


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

@router.get("/recipes")
def get_recipes(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    recipes = session.exec(select(DrinkRecipe).where(DrinkRecipe.enabled == True)).all()
    return [_recipe_out(r) for r in recipes]

@router.post("/make")
def make_drink(data: MakeDrinkRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == data.recipe_id)).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    serving_modes = _safe_load_json(getattr(recipe, "serving_modes_json", "{}"), {})
    selected_mode = data.serving_mode.value
    if selected_mode not in serving_modes:
        selected_mode = "medium" if "medium" in serving_modes else (next(iter(serving_modes), "medium"))

    available_glasses = _safe_load_json(getattr(recipe, "glass_options_json", "[]"), [])
    selected_glass = data.glass_type
    if available_glasses and selected_glass not in available_glasses:
        raise HTTPException(status_code=400, detail="Tipo de vaso no disponible para esta receta")

    # 1. Sumamos la XP correcta de la receta y actualizamos el nivel (1 nivel cada 100 XP)
    user.xp += recipe.xp_reward
    user.level = (user.xp // 100) + 1  
    session.add(user)
    
    # 2. Registramos la consumición en el historial de la máquina
    event = MachineEvent(
        event_type="drink_made",
        status="done",
        detail=f"{user.username} preparó {recipe.name} [{selected_mode}] ({selected_glass})"
    )
    session.add(event)

    dispense = Dispense(
        user_id=user.id,
        recipe_id=recipe.id,
        action="make_drink",
        status="done",
        xp_earned=recipe.xp_reward,
    )
    session.add(dispense)
    session.commit()
    
    return {"message": "Bebida en preparación", "xp_earned": recipe.xp_reward}

@router.post("/repeat-last")
def repeat_last(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    last = session.exec(
        select(Dispense).where(Dispense.user_id == user.id).order_by(Dispense.created_at.desc())
    ).first()
    if not last:
        raise HTTPException(status_code=404, detail="No hay cubatas previos")
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == last.recipe_id)).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta anterior no encontrada")
    return {"ok": True, "message": f"Repitiendo {recipe.name}", "recipe_id": recipe.id}