from fastapi import APIRouter, HTTPException, Depends, Request
from app.routers.users import get_admin_user
from app.config import get_db
from sqlalchemy.orm import Session
from app.models.models import Deposit, Ingredient

router = APIRouter()


@router.get('/status')
async def get_status(request: Request):
    uart = request.app.state.uart
    return await uart.get_status()


@router.post('/clean')
async def clean(request: Request):
    uart = request.app.state.uart
    try:
        return await uart.clean()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/stop')
async def stop(request: Request):
    uart = request.app.state.uart
    return await uart.stop()


@router.post('/temp')
async def set_temp(request: Request, payload: dict):
    target = payload.get('temperature')
    if target is None:
        raise HTTPException(status_code=400, detail='temperature required')
    uart = request.app.state.uart
    return await uart.set_temp(target)


@router.get('/ingredients')
def list_ingredients(db: Session = Depends(get_db)):
    ingredients = db.query(Ingredient).all()
    return [{"id": i.id, "name": i.name, "description": i.description} for i in ingredients]


@router.get('/deposits')
def list_deposits(admin_user=Depends(get_admin_user), db: Session = Depends(get_db)):
    deposits = db.query(Deposit).order_by(Deposit.slot).all()
    return [
        {
            "id": d.id,
            "slot": d.slot,
            "ingredient_id": d.ingredient_id,
            "ingredient_name": d.ingredient.name if d.ingredient else None,
            "level_ml": d.level_ml,
            "capacity_ml": d.capacity_ml,
        }
        for d in deposits
    ]


@router.patch('/deposits/{deposit_id}')
def update_deposit(deposit_id: int, payload: dict, admin_user=Depends(get_admin_user), db: Session = Depends(get_db)):
    deposit = db.query(Deposit).filter(Deposit.id == deposit_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail='Deposit not found')
    if payload.get('ingredient_id') is not None:
        ingredient = db.query(Ingredient).filter(Ingredient.id == payload.get('ingredient_id')).first()
        if not ingredient:
            raise HTTPException(status_code=404, detail='Ingredient not found')
        deposit.ingredient_id = ingredient.id
    if payload.get('level_ml') is not None:
        deposit.level_ml = int(payload.get('level_ml'))
    if payload.get('capacity_ml') is not None:
        deposit.capacity_ml = int(payload.get('capacity_ml'))
    db.commit()
    db.refresh(deposit)
    return {
        "id": deposit.id,
        "slot": deposit.slot,
        "ingredient_id": deposit.ingredient_id,
        "ingredient_name": deposit.ingredient.name if deposit.ingredient else None,
        "level_ml": deposit.level_ml,
        "capacity_ml": deposit.capacity_ml,
    }
