from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class MakeDrinkRequest(BaseModel):
    recipe_id: int

class MachineActionRequest(BaseModel):
    action: str
