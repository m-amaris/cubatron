from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import User, DrinkRecipe, MachineConfig, Tank
from app.security import hash_password

def seed():
    create_db_and_tables()
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.username == "miguel")).first()
        if not admin:
            session.add(User(
                username="miguel",
                full_name="Miguel",
                password_hash=hash_password("Cubatron2026!"),
                role="admin",
                favorite_mix="Ron cola",
                xp=120,
                level=3
            ))

        if not session.exec(select(DrinkRecipe)).first():
            session.add(DrinkRecipe(
                name="Ron Cola",
                description="Clásico cubata equilibrado",
                mixer="Cola",
                spirit="Ron",
                spirit_ml=50,
                mixer_ml=150
            ))
            session.add(DrinkRecipe(
                name="Gin Lemon",
                description="Gin con refresco de limón",
                mixer="Lemon",
                spirit="Gin",
                spirit_ml=50,
                mixer_ml=150
            ))

        if not session.exec(select(MachineConfig)).first():
            session.add(MachineConfig())

        if not session.exec(select(Tank)).first():
            session.add(Tank(slot=1, name="Deposito 1", content="Ron", capacity_ml=2000, current_ml=1600))
            session.add(Tank(slot=2, name="Deposito 2", content="Cola", capacity_ml=2000, current_ml=1800))
            session.add(Tank(slot=3, name="Deposito 3", content="Gin", capacity_ml=2000, current_ml=900))
            session.add(Tank(slot=4, name="Deposito 4", content="Lemon", capacity_ml=2000, current_ml=1500))

        session.commit()

if __name__ == "__main__":
    seed()
