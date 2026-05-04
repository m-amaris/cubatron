import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import engine, Base, SessionLocal
from app.models import models
from app.services.uart_service import UARTService
from app.routers import auth, users, drinks, machine, history
from app.services.auth_service import get_password_hash

def create_app() -> FastAPI:
    app = FastAPI(title='Cubatron')

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # include routers
    app.include_router(auth.router, prefix='/api/auth')
    app.include_router(users.router, prefix='/api/users')
    app.include_router(drinks.router, prefix='/api')
    app.include_router(machine.router, prefix='/api/machine')
    app.include_router(history.router, prefix='/api')

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    # serve frontend static build if present
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
    if os.path.isdir(static_dir):
        app.mount('/', StaticFiles(directory=static_dir, html=True), name='frontend')

    return app


app = create_app()


@app.on_event('startup')
def on_startup():
    # create DB
    Base.metadata.create_all(bind=engine)

    # ensure admin user
    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(models.User.username == os.getenv('CUBATRON_ADMIN_USER', 'admin')).first()
        if not admin_user:
            admin = models.User(
                username=os.getenv('CUBATRON_ADMIN_USER', 'admin'),
                hashed_password=get_password_hash(os.getenv('CUBATRON_ADMIN_PASS', 'admin')),
                is_admin=True
            )
            db.add(admin)
            db.commit()
        # create some default cups, ingredients, deposits and recipes if not present
        if db.query(models.Cup).count() == 0:
            db.add_all([
                models.Cup(name='Small', capacity_ml=180, description='Small glass'),
                models.Cup(name='Medium', capacity_ml=300, description='Standard glass'),
                models.Cup(name='Large', capacity_ml=450, description='Large glass')
            ])
            db.commit()

        if db.query(models.Ingredient).count() == 0:
            ing1 = models.Ingredient(name='Rum')
            ing2 = models.Ingredient(name='Cola')
            ing3 = models.Ingredient(name='Lime')
            ing4 = models.Ingredient(name='Syrup')
            db.add_all([ing1, ing2, ing3, ing4])
            db.commit()
            # assign deposits
            db.add_all([
                models.Deposit(slot=1, ingredient_id=ing1.id, level_ml=1000, capacity_ml=1000),
                models.Deposit(slot=2, ingredient_id=ing2.id, level_ml=1000, capacity_ml=1000),
                models.Deposit(slot=3, ingredient_id=ing3.id, level_ml=1000, capacity_ml=1000),
                models.Deposit(slot=4, ingredient_id=ing4.id, level_ml=1000, capacity_ml=1000),
            ])
            db.commit()

        if db.query(models.Recipe).count() == 0:
            # Example recipe: simple 2-ingredient mix
            db.add(models.Recipe(name='Simple Mix', description='Rum & Cola', composition={"1": 50, "2": 50}))
            db.commit()
    finally:
        db.close()

    # init UART service
    dry = os.getenv('CUBATRON_UART_DRY_RUN', 'true').lower() in ('1', 'true', 'yes')
    app.state.uart = UARTService(dry_run=dry)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)
