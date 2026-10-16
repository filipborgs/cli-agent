from sqlalchemy import Engine, inspect
from sqlalchemy.orm import configure_mappers


def test_registered_models_match_migrated_tables(admin_engine: Engine) -> None:
    from clinic_api.db.base import Base
    from clinic_api.db.models.registry import register_models

    register_models()
    register_models()
    configure_mappers()
    assert set(Base.metadata.tables) == set(inspect(admin_engine).get_table_names()) - {
        "alembic_version"
    }
