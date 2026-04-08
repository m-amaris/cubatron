from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from typing import List
from datetime import datetime, timedelta
from threading import Lock
import re
from app.database import get_session
from app.models import MachineConfig, Tank, MachineEvent
from app.config import UART_ENABLED
from app.uart import (
    build_clean_command,
    build_status_command,
    build_stop_command,
    build_temp_command,
    get_last_uart_write,
    send_uart_command,
)

router = APIRouter()

MACHINE_STATUS = "ONLINE"
_STATUS_LOCK = Lock()

class TankUpdate(BaseModel):
    id: int
    name: str
    liquid_type: str
    current_ml: int  # <-- AHORA SÍ: Coincide exactamente con lo que manda la web


class TempUpdate(BaseModel):
    target_c: float = Field(ge=-20, le=40)

@router.get("/status")
def status(session: Session = Depends(get_session)):
    config = session.exec(select(MachineConfig)).first()
    tanks = session.exec(select(Tank)).all()
    
    cutoff = datetime.utcnow() - timedelta(hours=24)
    events_24h = session.exec(
        select(MachineEvent).where(
            MachineEvent.event_type == "drink_made",
            MachineEvent.created_at >= cutoff,
        )
    ).all()
    drinks_24h = len(events_24h)
    
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


@router.get("/uart/last")
def uart_last_write():
    return {"ok": True, "last": get_last_uart_write()}


@router.post("/uart/status")
def uart_status():
    uart_payload = send_uart_command(build_status_command())
    if UART_ENABLED and not uart_payload.get("ok"):
        error_detail = uart_payload.get("error") or "Error UART"
        raise HTTPException(status_code=503, detail=f"No se pudo escribir en UART: {error_detail}")
    return {"ok": True, "uart": uart_payload}


@router.post("/stop")
def stop_machine(session: Session = Depends(get_session)):
    global MACHINE_STATUS
    with _STATUS_LOCK:
        MACHINE_STATUS = "BUSY"
    try:
        uart_payload = send_uart_command(build_stop_command())
        if UART_ENABLED and not uart_payload.get("ok"):
            error_detail = uart_payload.get("error") or "Error UART"
            raise HTTPException(status_code=503, detail=f"No se pudo escribir en UART: {error_detail}")

        session.add(MachineEvent(event_type="stop", status="done", detail="Parada de emergencia enviada"))
        session.commit()
        return {"ok": True, "message": "Parada enviada", "uart": uart_payload}
    finally:
        with _STATUS_LOCK:
            MACHINE_STATUS = "ONLINE"


@router.post("/temp")
def set_temperature(data: TempUpdate, session: Session = Depends(get_session)):
    global MACHINE_STATUS
    with _STATUS_LOCK:
        MACHINE_STATUS = "BUSY"
    try:
        uart_payload = send_uart_command(build_temp_command(data.target_c))
        if UART_ENABLED and not uart_payload.get("ok"):
            error_detail = uart_payload.get("error") or "Error UART"
            raise HTTPException(status_code=503, detail=f"No se pudo escribir en UART: {error_detail}")

        config = session.exec(select(MachineConfig)).first()
        if not config:
            config = MachineConfig()
        config.serving_temperature = float(data.target_c)
        session.add(config)
        session.add(MachineEvent(event_type="temp", status="done", detail=f"TEMP set {data.target_c}"))
        session.commit()
        return {"ok": True, "temperature": config.serving_temperature, "uart": uart_payload}
    finally:
        with _STATUS_LOCK:
            MACHINE_STATUS = "ONLINE"


@router.post("/tanks/update")
def update_tanks(tanks_data: List[TankUpdate], session: Session = Depends(get_session)):
    global MACHINE_STATUS
    with _STATUS_LOCK:
        MACHINE_STATUS = "BUSY"
    try:
        for t_data in tanks_data:
            tank = session.exec(select(Tank).where(Tank.id == t_data.id)).first()
            if tank:
                tank.name = t_data.name
                tank.content = t_data.name
                tank.liquid_type = t_data.liquid_type

                # El dato t_data.current_ml trae el % (ej: 80). Lo pasamos a mililitros reales para la BD.
                capacity = tank.capacity_ml if getattr(tank, "capacity_ml", None) else 1000
                tank.current_ml = int((t_data.current_ml / 100.0) * capacity)

                session.add(tank)

        session.commit()
        return {"message": "Depósitos actualizados"}
    finally:
        with _STATUS_LOCK:
            MACHINE_STATUS = "ONLINE"

@router.post("/action/{action_name}")
def perform_action(action_name: str, session: Session = Depends(get_session)):
    global MACHINE_STATUS
    if action_name not in {"prime", "clean"} and not re.fullmatch(r"purge_tank_\d+", action_name):
        raise HTTPException(status_code=400, detail="Acción no permitida")

    with _STATUS_LOCK:
        MACHINE_STATUS = "BUSY"
    try:
        uart_payload = None
        if action_name == "clean":
            uart_payload = send_uart_command(build_clean_command())
        elif action_name.startswith("purge_tank_"):
            slot = int(action_name.split("_")[-1])
            uart_payload = send_uart_command(build_clean_command(slot))

        if UART_ENABLED and uart_payload is not None and not uart_payload.get("ok"):
            error_detail = uart_payload.get("error") or "Error UART"
            raise HTTPException(status_code=503, detail=f"No se pudo escribir en UART: {error_detail}")

        session.add(MachineEvent(event_type=action_name, status="done", detail=f"Acción {action_name} ejecutada"))
        session.commit()
        return {"ok": True, "message": f"{action_name.capitalize()} completado", "uart": uart_payload}
    finally:
        with _STATUS_LOCK:
            MACHINE_STATUS = "ONLINE"