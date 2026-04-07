from sqlmodel import Session, select
import json
import os
import secrets
from app.database import engine, create_db_and_tables
from app.models import User, DrinkRecipe, MachineConfig, Tank, GlassType
from app.security import hash_password

def seed():
    create_db_and_tables()
    with Session(engine) as session:
        bootstrap_user = os.getenv("CUBATRON_BOOTSTRAP_ADMIN_USER")
        bootstrap_pass = os.getenv("CUBATRON_BOOTSTRAP_ADMIN_PASSWORD")

        admin = (
            session.exec(select(User).where(User.username == bootstrap_user)).first()
            if bootstrap_user
            else None
        )
        if bootstrap_user and bootstrap_pass and not admin:
            session.add(User(
                username=bootstrap_user,
                full_name=os.getenv("CUBATRON_BOOTSTRAP_ADMIN_FULLNAME", "Administrador"),
                password_hash=hash_password(bootstrap_pass),
                role="admin",
                favorite_mix="",
                xp=0,
                level=1
            ))

        if not bootstrap_user and not session.exec(select(User)).first():
            generated_password = secrets.token_urlsafe(12)
            session.add(
                User(
                    username="admin",
                    full_name="Administrador",
                    password_hash=hash_password(generated_password),
                    role="admin",
                    favorite_mix="",
                    xp=0,
                    level=1,
                )
            )
            print(
                "[CUBATRON] Usuario admin inicial creado: username=admin "
                f"password={generated_password}"
            )

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

        default_glasses = [
            {"key": "shot", "name": "Shot", "icon": "🧪", "capacity_ml": 60, "enabled": True},
            {"key": "rocks", "name": "Rocks", "icon": "🥃", "capacity_ml": 180, "enabled": True},
            {"key": "coupe", "name": "Coupe", "icon": "🍸", "capacity_ml": 200, "enabled": True},
            {"key": "highball", "name": "Highball", "icon": "🥤", "capacity_ml": 300, "enabled": True},
            {"key": "hurricane", "name": "Hurricane", "icon": "🍹", "capacity_ml": 420, "enabled": True},
        ]

        for defaults in default_glasses:
            glass = session.exec(select(GlassType).where(GlassType.key == defaults["key"])).first()
            if not glass:
                session.add(GlassType(**defaults))
                continue
            changed = False
            for field in ("name", "icon", "capacity_ml"):
                if getattr(glass, field) in (None, "", 0):
                    setattr(glass, field, defaults[field])
                    changed = True
            if changed:
                session.add(glass)

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
