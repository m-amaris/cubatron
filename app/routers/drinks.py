from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
import json
from app.database import get_session
from app.models import User, DrinkRecipe, Dispense, MachineEvent, GlassType
from app.schemas import MakeDrinkRequest
from app.dependencies import get_current_user

router = APIRouter()

DEFAULT_GLASSES = {
    "shot": {"name": "Shot", "icon": "🧪", "capacity_ml": 60},
    "rocks": {"name": "Rocks", "icon": "🥃", "capacity_ml": 180},
    "coupe": {"name": "Coupe", "icon": "🍸", "capacity_ml": 200},
    "highball": {"name": "Highball", "icon": "🥤", "capacity_ml": 300},
    "hurricane": {"name": "Hurricane", "icon": "🍹", "capacity_ml": 420},
}

MODE_XP_MULTIPLIER = {
    "low": 0.9,
    "medium": 1.0,
    "high": 1.2,
    "extreme": 1.4,
    "custom": 1.0,
}


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


def _active_glass_catalog(session: Session) -> dict[str, dict]:
    rows = session.exec(select(GlassType).where(GlassType.enabled == True)).all()
    if not rows:
        return DEFAULT_GLASSES
    out: dict[str, dict] = {}
    for row in rows:
        out[row.key] = {
            "name": row.name,
            "icon": row.icon,
            "capacity_ml": int(row.capacity_ml),
        }
    return out


def _available_recipe_glasses(recipe: DrinkRecipe, glass_catalog: dict[str, dict]) -> list[str]:
    requested = _safe_load_json(getattr(recipe, "glass_options_json", "[]"), [])
    if not isinstance(requested, list):
        requested = []

    filtered = [key for key in requested if key in glass_catalog]
    if filtered:
        return filtered
    return list(glass_catalog.keys())


def _glass_capacity_ml(glass_catalog: dict[str, dict], glass_type: str) -> int:
    if glass_type in glass_catalog:
        return int(glass_catalog[glass_type].get("capacity_ml", 300))
    if "highball" in glass_catalog:
        return int(glass_catalog["highball"].get("capacity_ml", 300))
    first = next(iter(glass_catalog.values()), {"capacity_ml": 300})
    return int(first.get("capacity_ml", 300))


def _compute_xp(base_xp: int, capacity_ml: int, serving_mode: str) -> int:
    glass_mult = max(0.6, min(2.2, capacity_ml / 300.0))
    mode_mult = MODE_XP_MULTIPLIER.get(serving_mode, 1.0)
    return max(1, int(round(base_xp * glass_mult * mode_mult)))


def _compute_liquid_breakdown(profile: dict[str, float], total_ml: int) -> list[dict]:
    safe_items = []
    for liq, raw_pct in (profile or {}).items():
        try:
            pct = float(raw_pct)
        except Exception:
            pct = 0.0
        safe_items.append((str(liq), max(0.0, pct)))

    pct_sum = sum(pct for _, pct in safe_items)
    if not safe_items or pct_sum <= 0:
        return []

    breakdown = []
    consumed = 0
    for idx, (liq, pct) in enumerate(safe_items):
        if idx == len(safe_items) - 1:
            ml = max(0, total_ml - consumed)
        else:
            ml = int(round(total_ml * (pct / pct_sum)))
            consumed += ml
        breakdown.append({"liquid": liq, "pct": round(pct, 2), "ml": ml})
    return breakdown


def _normalize_custom_profile(raw_profile, fallback_profile: dict[str, float] | None = None) -> dict[str, float]:
    safe_profile = {}
    if isinstance(raw_profile, dict):
        for liquid, raw_pct in raw_profile.items():
            try:
                pct = float(raw_pct)
            except Exception:
                pct = 0.0
            safe_profile[str(liquid)] = max(0.0, pct)

    if safe_profile:
        return safe_profile

    fallback_profile = fallback_profile or {}
    safe_fallback = {}
    for liquid, raw_pct in fallback_profile.items():
        try:
            pct = float(raw_pct)
        except Exception:
            pct = 0.0
        safe_fallback[str(liquid)] = max(0.0, pct)
    return safe_fallback


def _resolve_service_selection(
    recipe: DrinkRecipe,
    session: Session,
    serving_mode: str,
    glass_type: str,
    custom_serving_profile: dict[str, float] | None = None,
) -> dict:
    serving_modes = _safe_load_json(getattr(recipe, "serving_modes_json", "{}"), {})
    selected_mode = serving_mode
    if selected_mode != "custom" and selected_mode not in serving_modes:
        selected_mode = "medium" if "medium" in serving_modes else (next(iter(serving_modes), "medium"))

    glass_catalog = _active_glass_catalog(session)
    available_glasses = _available_recipe_glasses(recipe, glass_catalog)
    selected_glass = glass_type
    if available_glasses and selected_glass not in available_glasses:
        raise HTTPException(status_code=400, detail="Tipo de vaso no disponible para esta receta")

    if selected_glass not in glass_catalog:
        raise HTTPException(status_code=400, detail="Tipo de vaso no configurado")

    total_ml = _glass_capacity_ml(glass_catalog, selected_glass)
    xp_earned = _compute_xp(recipe.xp_reward, total_ml, selected_mode)
    profile = {}
    if selected_mode == "custom":
        fallback_mode = "medium" if isinstance(serving_modes, dict) and "medium" in serving_modes else (next(iter(serving_modes), None) if isinstance(serving_modes, dict) and serving_modes else None)
        fallback_profile = serving_modes.get(fallback_mode, {}) if fallback_mode else {}
        profile = _normalize_custom_profile(custom_serving_profile, fallback_profile=fallback_profile)
        if not profile:
            raise HTTPException(status_code=400, detail="Perfil personalizado no válido")
        if sum(profile.values()) <= 0:
            raise HTTPException(status_code=400, detail="Perfil personalizado no válido")
    else:
        profile = serving_modes.get(selected_mode, {}) if isinstance(serving_modes, dict) else {}
    liquid_breakdown = _compute_liquid_breakdown(profile, total_ml)
    if selected_mode == "custom" and not liquid_breakdown:
        raise HTTPException(status_code=400, detail="Perfil personalizado no válido")
    glass_info = glass_catalog.get(selected_glass, {})

    return {
        "xp_earned": xp_earned,
        "glass_capacity_ml": total_ml,
        "total_ml": total_ml,
        "glass_type": selected_glass,
        "glass_name": glass_info.get("name", selected_glass),
        "glass_icon": glass_info.get("icon", "🥤"),
        "serving_mode": selected_mode,
        "liquid_breakdown": liquid_breakdown,
    }


@router.get("/glasses")
def get_glasses(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    catalog = _active_glass_catalog(session)
    return [
        {
            "key": key,
            "name": value.get("name", key),
            "icon": value.get("icon", "🥤"),
            "capacity_ml": int(value.get("capacity_ml", 300)),
        }
        for key, value in sorted(catalog.items(), key=lambda item: item[1].get("name", item[0]).lower())
    ]

@router.get("/recipes")
def get_recipes(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    recipes = session.exec(select(DrinkRecipe).where(DrinkRecipe.enabled == True)).all()
    return [_recipe_out(r) for r in recipes]


@router.post("/preview")
def preview_drink(
    data: MakeDrinkRequest,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == data.recipe_id)).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")

    return _resolve_service_selection(
        recipe=recipe,
        session=session,
        serving_mode=data.serving_mode.value,
        glass_type=data.glass_type,
        custom_serving_profile=data.custom_serving_profile,
    )

@router.post("/make")
def make_drink(data: MakeDrinkRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == data.recipe_id)).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")

    service_data = _resolve_service_selection(
        recipe=recipe,
        session=session,
        serving_mode=data.serving_mode.value,
        glass_type=data.glass_type,
        custom_serving_profile=data.custom_serving_profile,
    )
    xp_earned = int(service_data["xp_earned"])
    total_ml = int(service_data["total_ml"])
    selected_glass = str(service_data["glass_type"])
    selected_mode = str(service_data["serving_mode"])
    liquid_breakdown = service_data["liquid_breakdown"]

    # 1. Sumamos la XP final según vaso y modo, y actualizamos nivel (1 nivel cada 100 XP)
    user.xp += xp_earned
    user.level = (user.xp // 100) + 1  
    session.add(user)
    
    # 2. Registramos la consumición en el historial de la máquina
    event = MachineEvent(
        event_type="drink_made",
        status="done",
        detail=f"{user.username} preparó {recipe.name} [{selected_mode}] ({selected_glass}, {total_ml}ml)"
    )
    session.add(event)

    dispense = Dispense(
        user_id=user.id,
        recipe_id=recipe.id,
        action="make_drink",
        status="done",
        xp_earned=xp_earned,
        glass_type=selected_glass,
        serving_mode=selected_mode,
    )
    session.add(dispense)
    session.commit()
    
    return {
        "message": "Bebida en preparación",
        "xp_earned": xp_earned,
        "glass_capacity_ml": total_ml,
        "total_ml": total_ml,
        "glass_type": selected_glass,
        "serving_mode": selected_mode,
        "liquid_breakdown": liquid_breakdown,
    }

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