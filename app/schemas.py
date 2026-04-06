from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class MakeDrinkRequest(BaseModel):
    recipe_id: int
    serving_mode: str = "medium"
    glass_type: str = "highball"

class MachineActionRequest(BaseModel):
    action: str
