from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import Optional
from app.database import get_session
from app.models import User, Tank, DrinkRecipe, MachineEvent
from app.security import hash_password

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
    username: str
    password: str
    full_name: str
    role: str

class RecipeCreate(BaseModel):
    name: str
    description: str
    ingredients: str
    xp_reward: int
    
class RecipeUpdate(BaseModel):
    name: str
    description: str
    ingredients: str  # Ej: "Ron, Cola"
    xp_reward: int

@router.get("/overview")
def overview(session: Session = Depends(get_session)):
    return {
        "users": len(session.exec(select(User)).all()),
        "recipes": len(session.exec(select(DrinkRecipe)).all()),
        "tanks": len(session.exec(select(Tank)).all()),
        "events": len(session.exec(select(MachineEvent)).all())
    }

@router.get("/settings")
def get_settings():
    return SYSTEM_SETTINGS

@router.post("/settings")
def update_settings(settings: dict):
    global SYSTEM_SETTINGS
    SYSTEM_SETTINGS.update(settings)
    return SYSTEM_SETTINGS

@router.post("/users/create")
def create_user(user_data: UserCreate, session: Session = Depends(get_session)):
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
def get_admin_recipes(session: Session = Depends(get_session)):
    return session.exec(select(DrinkRecipe)).all()

@router.post("/recipes/create")
def create_recipe(data: RecipeCreate, session: Session = Depends(get_session)):
    recipe = DrinkRecipe(
        name=data.name,
        description=data.description,
        ingredients=data.ingredients,
        xp_reward=data.xp_reward
    )
    session.add(recipe)
    session.commit()
    return {"message": "Receta creada"}


@router.post("/recipes/{recipe_id}")
def update_recipe(recipe_id: int, data: RecipeUpdate, session: Session = Depends(get_session)):
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == recipe_id)).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    recipe.name = data.name
    recipe.description = data.description
    # Asumimos que has añadido estos campos a tu modelo DrinkRecipe en models.py
    # recipe.ingredients = data.ingredients 
    # recipe.xp_reward = data.xp_reward
    
    session.add(recipe)
    session.commit()
    return {"message": "Receta actualizada"}



@router.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int, session: Session = Depends(get_session)):
    recipe = session.exec(select(DrinkRecipe).where(DrinkRecipe.id == recipe_id)).first()
    if recipe:
        session.delete(recipe)
        session.commit()
    return {"message": "Receta eliminada"}