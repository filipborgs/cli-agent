from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, text
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.orm import Session

from clinic_api.domain.identity.context import AccessContext
from clinic_api.domain.shared.errors import AccessDenied


def create_engine(database_url: str) -> Engine:
    return sqlalchemy_create_engine(database_url, pool_pre_ping=True)


class TenantSession(Session):
    context: AccessContext


@contextmanager
def tenant_session(engine: Engine, context: AccessContext) -> Iterator[TenantSession]:
    session = TenantSession(engine)
    session.context = context
    try:
        with session.begin():
            session.execute(
                text("SELECT set_config('app.user_id', :user_id, true)"),
                {"user_id": str(context.user_id)},
            )
            session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(context.tenant_id)},
            )
            membership = session.scalar(
                text(
                    "SELECT 1 FROM user_tenant WHERE tenant_id = :tenant_id AND user_id = :user_id AND active AND role = 'admin'"
                ),
                {"tenant_id": context.tenant_id, "user_id": context.user_id},
            )
            if membership is None:
                raise AccessDenied("Administrative membership is required")
            yield session
    finally:
        session.close()
