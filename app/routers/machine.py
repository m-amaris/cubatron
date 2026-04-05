from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import List
from app.database import get_session
from app.models import MachineConfig, Tank, MachineEvent

router = APIRouter()

MACHINE_STATUS = "ONLINE"

class TankUpdate(BaseModel):
    id: int
    name: str
    liquid_type: str
    current_ml: int  # <-- AHORA SÍ: Coincide exactamente con lo que manda la web
@router.get("/status")

@router.get("/status")
def status(session: Session = Depends(get_session)):
    config = session.exec(select(MachineConfig)).first()
    tanks = session.exec(select(Tank)).all()
    
    # Contamos todas las bebidas preparadas
    events = session.exec(select(MachineEvent).where(MachineEvent.event_type == "drink_made")).all()
    drinks_24h = len(events) 
    
    tanks_out = []
    for t in tanks:
        t_dict = t.model_dump() if hasattr(t, "model_dump") else t.dict()
        capacity = t.capacity_ml if getattr(t, "capacity_ml", None) else 1000
        t_dict["current_level"] = int((t.current_ml / capacity) * 100) if t.current_ml else 0
        tanks_out.append(t_dict)
        
    return {
        "status": MACHINE_STATUS,
        "temperature": config.serving_temperature if config else 7.0,
        "drinks_24h": drinks_24h,  # <-- Enviamos el dato al frontend
        "tanks": tanks_out
    }


@router.post("/tanks/update")
def update_tanks(tanks_data: List[TankUpdate], session: Session = Depends(get_session)):
    global MACHINE_STATUS
    MACHINE_STATUS = "BUSY" 
    
    for t_data in tanks_data:
        tank = session.exec(select(Tank).where(Tank.id == t_data.id)).first()
        if tank:
            tank.name = t_data.name
            tank.liquid_type = t_data.liquid_type 
            
            # El dato t_data.current_ml trae el % (ej: 80). Lo pasamos a mililitros reales para la BD.
            capacity = tank.capacity_ml if getattr(tank, "capacity_ml", None) else 1000
            tank.current_ml = int((t_data.current_ml / 100.0) * capacity)
            
            session.add(tank)
    
    session.commit()
    MACHINE_STATUS = "ONLINE"
    return {"message": "Depósitos actualizados"}

@router.post("/action/{action_name}")
def perform_action(action_name: str, session: Session = Depends(get_session)):
    global MACHINE_STATUS
    MACHINE_STATUS = "BUSY"
    session.add(MachineEvent(event_type=action_name, status="done", detail=f"Acción {action_name} ejecutada"))
    session.commit()
    MACHINE_STATUS = "ONLINE"
    return {"ok": True, "message": f"{action_name.capitalize()} completado"}