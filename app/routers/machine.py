from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.models import MachineConfig, Tank, MachineEvent

router = APIRouter()

@router.get("/status")
def status(session: Session = Depends(get_session)):
    config = session.exec(select(MachineConfig)).first()
    tanks = session.exec(select(Tank)).all()
    return {
        "status": "ready",
        "temperature": config.serving_temperature if config else 7.0,
        "tanks": tanks
    }

@router.post("/purge")
def purge(session: Session = Depends(get_session)):
    session.add(MachineEvent(event_type="purge", status="done", detail="Purgado manual"))
    session.commit()
    return {"ok": True, "message": "Purgado completado"}

@router.post("/prime")
def prime(session: Session = Depends(get_session)):
    session.add(MachineEvent(event_type="prime", status="done", detail="Cebado manual"))
    session.commit()
    return {"ok": True, "message": "Cebado completado"}

@router.post("/clean")
def clean(session: Session = Depends(get_session)):
    session.add(MachineEvent(event_type="clean", status="done", detail="Limpieza manual"))
    session.commit()
    return {"ok": True, "message": "Limpieza completada"}
