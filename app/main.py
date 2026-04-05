from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import create_db_and_tables
from app.seed import seed
from app.routers import auth, users, drinks, machine, admin, web

app = FastAPI(title="Cubatron API")

app.mount("/static", StaticFiles(directory="/opt/cubatron/app/static"), name="static")

@app.on_event("startup")
def startup():
    create_db_and_tables()
    seed()

app.include_router(web.router)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(drinks.router, prefix="/api/drinks", tags=["drinks"])
app.include_router(machine.router, prefix="/api/machine", tags=["machine"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/health")
def health():
    return {"ok": True}
