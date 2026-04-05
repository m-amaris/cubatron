from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, Tank, DrinkRecipe, MachineEvent

router = APIRouter()

@router.get("/overview")
def overview(session: Session = Depends(get_session)):
    return {
        "users": len(session.exec(select(User)).all()),
        "recipes": len(session.exec(select(DrinkRecipe)).all()),
        "tanks": len(session.exec(select(Tank)).all()),
        "events": len(session.exec(select(MachineEvent)).all())
    }
