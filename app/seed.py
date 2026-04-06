from sqlmodel import Session, select
import json
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

        default_recipes = [
            {
                "name": "Ron Cola",
                "description": "Clásico cubata equilibrado",
                "ingredients": "Ron, CocaCola",
                "xp_reward": 150,
                "enabled": True,
                "glass_options_json": json.dumps(["highball", "rocks"]),
                "serving_modes_json": json.dumps({
                    "low": {"Ron": 30, "CocaCola": 70},
                    "medium": {"Ron": 40, "CocaCola": 60},
                    "high": {"Ron": 50, "CocaCola": 50},
                    "extreme": {"Ron": 65, "CocaCola": 35},
                }),
            },
            {
                "name": "Gin Lemon",
                "description": "Gin con refresco de limón",
                "ingredients": "Ginebra, Limón",
                "xp_reward": 150,
                "enabled": True,
                "glass_options_json": json.dumps(["highball", "coupe"]),
                "serving_modes_json": json.dumps({
                    "low": {"Ginebra": 30, "Limón": 70},
                    "medium": {"Ginebra": 40, "Limón": 60},
                    "high": {"Ginebra": 50, "Limón": 50},
                    "extreme": {"Ginebra": 65, "Limón": 35},
                }),
            },
        ]

        for defaults in default_recipes:
            recipe = session.exec(
                select(DrinkRecipe).where(DrinkRecipe.name == defaults["name"])
            ).first()

            if not recipe:
                session.add(DrinkRecipe(**defaults))
                continue

            # Repair legacy/empty defaults in place to keep startup idempotent.
            if not (recipe.ingredients or "").strip():
                recipe.ingredients = defaults["ingredients"]
            if not (getattr(recipe, "glass_options_json", "") or "").strip():
                recipe.glass_options_json = defaults["glass_options_json"]
            if not (getattr(recipe, "serving_modes_json", "") or "").strip() or recipe.serving_modes_json == "{}":
                recipe.serving_modes_json = defaults["serving_modes_json"]
            if not recipe.description:
                recipe.description = defaults["description"]
            if not recipe.xp_reward:
                recipe.xp_reward = defaults["xp_reward"]
            session.add(recipe)

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
