from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.config import get_db
from app.models.models import Recipe, Cup, History
from app.routers.users import get_admin_user
from app.services.auth_service import decode_access_token

router = APIRouter()


@router.get('/drinks')
def list_drinks(db: Session = Depends(get_db)):
    recipes = db.query(Recipe).all()
    return [
        {"id": r.id, "name": r.name, "description": r.description, "composition": r.composition}
        for r in recipes
    ]


@router.get('/drinks/{drink_id}')
def get_drink(drink_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == drink_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail='Drink not found')
    return {"id": recipe.id, "name": recipe.name, "description": recipe.description, "composition": recipe.composition}


@router.post('/drinks')
def create_drink(payload: dict, admin_user=Depends(get_admin_user), db: Session = Depends(get_db)):
    name = payload.get('name')
    description = payload.get('description', '')
    composition = payload.get('composition')
    if not name or composition is None:
        raise HTTPException(status_code=400, detail='name and composition required')
    if db.query(Recipe).filter(Recipe.name == name).first():
        raise HTTPException(status_code=400, detail='Recipe name exists')
    recipe = Recipe(name=name, description=description, composition=composition)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return {"id": recipe.id, "name": recipe.name, "description": recipe.description, "composition": recipe.composition}


@router.patch('/drinks/{drink_id}')
def update_drink(drink_id: int, payload: dict, admin_user=Depends(get_admin_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == drink_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail='Recipe not found')
    if payload.get('name') is not None:
        if db.query(Recipe).filter(Recipe.name == payload.get('name'), Recipe.id != recipe.id).first():
            raise HTTPException(status_code=400, detail='Recipe name exists')
        recipe.name = payload.get('name')
    if payload.get('description') is not None:
        recipe.description = payload.get('description')
    if payload.get('composition') is not None:
        recipe.composition = payload.get('composition')
    db.commit()
    db.refresh(recipe)
    return {"id": recipe.id, "name": recipe.name, "description": recipe.description, "composition": recipe.composition}


@router.delete('/drinks/{drink_id}')
def delete_drink(drink_id: int, admin_user=Depends(get_admin_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == drink_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail='Recipe not found')
    db.delete(recipe)
    db.commit()
    return {"status": "deleted", "id": drink_id}


@router.get('/cups')
def list_cups(db: Session = Depends(get_db)):
    cups = db.query(Cup).all()
    return [{"id": c.id, "name": c.name, "capacity_ml": c.capacity_ml, "description": c.description} for c in cups]


@router.post('/cups')
def create_cup(payload: dict, admin_user=Depends(get_admin_user), db: Session = Depends(get_db)):
    name = payload.get('name')
    capacity_ml = payload.get('capacity_ml')
    description = payload.get('description', '')
    if not name or capacity_ml is None:
        raise HTTPException(status_code=400, detail='name and capacity_ml required')
    cup = Cup(name=name, capacity_ml=int(capacity_ml), description=description)
    db.add(cup)
    db.commit()
    db.refresh(cup)
    return {"id": cup.id, "name": cup.name, "capacity_ml": cup.capacity_ml, "description": cup.description}


@router.patch('/cups/{cup_id}')
def update_cup(cup_id: int, payload: dict, admin_user=Depends(get_admin_user), db: Session = Depends(get_db)):
    cup = db.query(Cup).filter(Cup.id == cup_id).first()
    if not cup:
        raise HTTPException(status_code=404, detail='Cup not found')
    if payload.get('name') is not None:
        cup.name = payload.get('name')
    if payload.get('capacity_ml') is not None:
        cup.capacity_ml = int(payload.get('capacity_ml'))
    if payload.get('description') is not None:
        cup.description = payload.get('description')
    db.commit()
    db.refresh(cup)
    return {"id": cup.id, "name": cup.name, "capacity_ml": cup.capacity_ml, "description": cup.description}


@router.delete('/cups/{cup_id}')
def delete_cup(cup_id: int, admin_user=Depends(get_admin_user), db: Session = Depends(get_db)):
    cup = db.query(Cup).filter(Cup.id == cup_id).first()
    if not cup:
        raise HTTPException(status_code=404, detail='Cup not found')
    db.delete(cup)
    db.commit()
    return {"status": "deleted", "id": cup_id}


@router.get('/ingredients')
def list_ingredients(db: Session = Depends(get_db)):
    from app.models.models import Ingredient
    ingredients = db.query(Ingredient).all()
    return [{"id": i.id, "name": i.name, "description": i.description} for i in ingredients]


@router.post('/drinks/make')
async def make_drink(payload: dict, request: Request, db: Session = Depends(get_db)):
    recipe_id = payload.get('recipe_id')
    cup_id = payload.get('cup_id')
    mode = payload.get('mode', 'medium')
    custom_ml = payload.get('custom_ml')

    if not recipe_id or not cup_id:
        raise HTTPException(status_code=400, detail='recipe_id and cup_id required')

    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    cup = db.query(Cup).filter(Cup.id == cup_id).first()
    if not recipe or not cup:
        raise HTTPException(status_code=404, detail='recipe or cup not found')

    mode_map = {'low': 0.75, 'medium': 1.0, 'high': 1.25, 'extreme': 1.5}
    if mode == 'custom':
        if not custom_ml:
            raise HTTPException(status_code=400, detail='custom_ml required for custom mode')
        total_ml = int(custom_ml)
    else:
        total_ml = int(round(cup.capacity_ml * mode_map.get(mode, 1.0)))

    # recipe.composition is mapping slot->percent
    comp = recipe.composition or {}
    if not comp:
        raise HTTPException(status_code=400, detail='recipe composition empty')

    distribution = {}
    for slot_str, percent in comp.items():
        try:
            percent_val = float(percent)
        except Exception:
            percent_val = 0.0
        ml = int(round(total_ml * (percent_val / 100.0)))
        distribution[str(slot_str)] = ml

    # check machine state
    uart = request.app.state.uart
    status = await uart.get_status()
    if status.get('state') != 'IDLE':
        raise HTTPException(status_code=409, detail='Machine is busy')

    # check levels
    levels = status.get('levels', [])
    for slot_str, ml in distribution.items():
        idx = int(slot_str) - 1
        if idx < 0 or idx >= len(levels) or levels[idx] < ml:
            raise HTTPException(status_code=400, detail=f'Insufficient level in slot {slot_str}')

    # user identification optional (try to decode Bearer token)
    auth = request.headers.get('authorization', '') or request.headers.get('Authorization', '')
    user_id = None
    if auth and auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
        try:
            payload = decode_access_token(token)
            user_id = payload.get('user_id') or payload.get('sub')
        except Exception:
            user_id = None

    # create history entry (pending) to be updated by UART service
    h = History(user_id=user_id, recipe_id=recipe.id, cup_id=cup.id, ml_total=total_ml, mode=mode, success=False)
    db.add(h)
    db.commit()
    db.refresh(h)

    # start machine
    try:
        await uart.make(distribution, history_id=h.id, user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "started", "history_id": h.id}
