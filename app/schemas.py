from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ServingMode(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    extreme = "extreme"

class LoginRequest(BaseModel):
    username: str
    password: str

class MakeDrinkRequest(BaseModel):
    recipe_id: int = Field(gt=0)
    serving_mode: ServingMode = ServingMode.medium
    glass_type: str = Field(min_length=1, max_length=20)

    @field_validator("glass_type")
    @classmethod
    def validate_glass_type(cls, value: str) -> str:
        allowed = {"highball", "rocks", "coupe", "hurricane", "shot"}
        normalized = value.lower().strip()
        if normalized not in allowed:
            raise ValueError("Tipo de vaso no permitido")
        return normalized

class MachineActionRequest(BaseModel):
    action: str
