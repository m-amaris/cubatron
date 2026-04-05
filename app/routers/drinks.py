from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
import jwt
from app.database import get_session
from app.models import User, DrinkRecipe, Dispense
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
def make_drink(payload: MakeDrinkRequest, session: Session = Depends(get_session), user: User = Depends(current_user)):
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == payload.recipe_id)).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")

    dispense = Dispense(user_id=user.id, recipe_id=recipe.id, action="make_drink", status="done", xp_earned=10)
    user.xp += 10
    user.level = 1 + user.xp // 100
    session.add(dispense)
    session.add(user)
    session.commit()
    session.refresh(user)

    return {"ok": True, "message": f"Cubatron preparando {recipe.name}", "xp": user.xp, "level": user.level}

@router.post("/repeat-last")
def repeat_last(session: Session = Depends(get_session), user: User = Depends(current_user)):
    last = session.exec(
        select(Dispense).where(Dispense.user_id == user.id).order_by(Dispense.created_at.desc())
    ).first()
    if not last:
        raise HTTPException(status_code=404, detail="No hay cubatas previos")
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == last.recipe_id)).first()
    return {"ok": True, "message": f"Repitiendo {recipe.name}", "recipe_id": recipe.id}
