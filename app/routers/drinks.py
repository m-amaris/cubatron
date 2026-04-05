from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
import jwt
from app.database import get_session
from app.models import User, DrinkRecipe, Dispense, MachineEvent
from app.schemas import MakeDrinkRequest
from app.config import SECRET_KEY, ALGORITHM

router = APIRouter()

def current_user(authorization: str = Header(None), session: Session = Depends(get_session)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.split(" ", 1)[1]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user = session.exec(select(User).where(User.id == payload["user_id"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user

@router.get("/recipes")
def get_recipes(session: Session = Depends(get_session)):
    return session.exec(select(DrinkRecipe).where(DrinkRecipe.enabled == True)).all()

@router.post("/make")
def make_drink(data: MakeDrinkRequest, session: Session = Depends(get_session), user: User = Depends(current_user)):
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == data.recipe_id)).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    # 1. Sumamos la XP correcta de la receta y actualizamos el nivel (1 nivel cada 100 XP)
    user.xp += recipe.xp_reward
    user.level = (user.xp // 100) + 1  
    session.add(user)
    
    # 2. Registramos la consumición en el historial de la máquina
    event = MachineEvent(
        event_type="drink_made",
        status="done",
        detail=f"{user.username} preparó {recipe.name}"
    )
    session.add(event)
    session.commit()
    
    return {"message": "Bebida en preparación", "xp_earned": recipe.xp_reward}

@router.post("/repeat-last")
def repeat_last(session: Session = Depends(get_session), user: User = Depends(current_user)):
    last = session.exec(
        select(Dispense).where(Dispense.user_id == user.id).order_by(Dispense.created_at.desc())
    ).first()
    if not last:
        raise HTTPException(status_code=404, detail="No hay cubatas previos")
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == last.recipe_id)).first()
    return {"ok": True, "message": f"Repitiendo {recipe.name}", "recipe_id": recipe.id}