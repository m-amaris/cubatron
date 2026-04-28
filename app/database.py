from sqlmodel import SQLModel, Session, create_engine
from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


def _is_sqlite() -> bool:
    return engine.url.get_backend_name() == "sqlite"


def _sqlite_add_column_if_missing(conn, table: str, column: str, ddl: str) -> None:
    cols = {
        row[1]
        for row in conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in cols:
        conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def _run_sqlite_compat_migrations() -> None:
    if not _is_sqlite():
        return

    with engine.begin() as conn:
        tables = {
            row[0]
            for row in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        if "drinkrecipe" in tables:
            _sqlite_add_column_if_missing(
                conn,
                "drinkrecipe",
                "ingredients",
                "ingredients TEXT NOT NULL DEFAULT ''",
            )
            _sqlite_add_column_if_missing(
                conn,
                "drinkrecipe",
                "xp_reward",
                "xp_reward INTEGER NOT NULL DEFAULT 150",
            )
            _sqlite_add_column_if_missing(
                conn,
                "drinkrecipe",
                "enabled",
                "enabled BOOLEAN NOT NULL DEFAULT 1",
            )
            _sqlite_add_column_if_missing(
                conn,
                "drinkrecipe",
                "glass_options_json",
                "glass_options_json TEXT NOT NULL DEFAULT '[\"highball\", \"rocks\", \"coupe\", \"hurricane\"]'",
            )
            _sqlite_add_column_if_missing(
                conn,
                "drinkrecipe",
                "serving_modes_json",
                "serving_modes_json TEXT NOT NULL DEFAULT '{}'",
            )

        if "user" in tables:
            _sqlite_add_column_if_missing(
                conn,
                "user",
                "theme_mode",
                "theme_mode TEXT NOT NULL DEFAULT 'dark'",
            )
            _sqlite_add_column_if_missing(
                conn,
                "user",
                "accent_color",
                "accent_color TEXT NOT NULL DEFAULT 'emerald'",
            )
            _sqlite_add_column_if_missing(
                conn,
                "user",
                "info",
                "info TEXT NOT NULL DEFAULT ''",
            )
            _sqlite_add_column_if_missing(
                conn,
                "user",
                "is_archived",
                "is_archived BOOLEAN NOT NULL DEFAULT 0",
            )
            _sqlite_add_column_if_missing(
                conn,
                "user",
                "archived_at",
                "archived_at DATETIME",
            )
            _sqlite_add_column_if_missing(
                conn,
                "user",
                "archived_by",
                "archived_by TEXT",
            )
            # Add pin_hash for touchscreen PIN login (nullable)
            _sqlite_add_column_if_missing(
                conn,
                "user",
                "pin_hash",
                "pin_hash TEXT",
            )

        if "dispense" in tables:
            _sqlite_add_column_if_missing(
                conn,
                "dispense",
                "glass_type",
                "glass_type TEXT",
            )
            _sqlite_add_column_if_missing(
                conn,
                "dispense",
                "serving_mode",
                "serving_mode TEXT",
            )


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    _run_sqlite_compat_migrations()

def get_session():
    with Session(engine) as session:
        yield session
