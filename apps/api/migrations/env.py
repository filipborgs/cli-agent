from alembic import context

from clinic_api.db.base import Base
from clinic_api.db.models.registry import register_models
from clinic_api.db.session import create_engine
from clinic_api.environment import EnvironmentVariable

register_models()
target_metadata = Base.metadata
database_url = EnvironmentVariable.MIGRATION_DATABASE_URL.required()

if context.is_offline_mode():
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()
