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
    glass_type: str = Field(min_length=1, max_length=32)

    @field_validator("glass_type")
    @classmethod
    def validate_glass_type(cls, value: str) -> str:
        normalized = value.lower().strip()
        if not normalized:
            raise ValueError("Tipo de vaso no permitido")
        if len(normalized) > 32:
            raise ValueError("Tipo de vaso no permitido")
        if not all(ch.isalnum() or ch in {"-", "_"} for ch in normalized):
            raise ValueError("Tipo de vaso no permitido")
        return normalized

class MachineActionRequest(BaseModel):
    action: str
