from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    full_name: str
    password_hash: str
    role: str = "user"
    avatar_url: Optional[str] = None
    favorite_mix: Optional[str] = None
    xp: int = 0
    level: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DrinkRecipe(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str
    ingredients: str = ""  # Ej: "CocaCola, Ron"
    xp_reward: int = 150   # Experiencia que da al prepararla
    enabled: bool = True
    glass_options_json: str = '["highball", "rocks", "coupe", "hurricane"]'
    serving_modes_json: str = '{}'

class Dispense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    recipe_id: int = Field(index=True)
    action: str = "make_drink"
    status: str = "done"
    xp_earned: int = 10
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MachineConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    serving_temperature: float = 7.0
    purge_seconds: int = 5
    prime_seconds: int = 3
    cleaning_seconds: int = 10
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Tank(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slot: int
    name: str
    content: str
    capacity_ml: int
    current_ml: int
    enabled: bool = True
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    liquid_type: str = "mixer"

class MachineEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str
    status: str = "done"
    detail: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
