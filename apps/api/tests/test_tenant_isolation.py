import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import ProgrammingError


def test_requires_active_admin_membership(factory, runtime_engine: Engine) -> None:
    from clinic_api.domain.shared.errors import AccessDenied

    permitted = factory.identity()
    other = factory.identity()
    forbidden = factory.context_for(permitted.user_id, other.tenant_id)

    from clinic_api.db.session import tenant_session

    with pytest.raises(AccessDenied), tenant_session(runtime_engine, forbidden):
        pass


def test_cross_tenant_read_and_write(factory, runtime_engine: Engine) -> None:
    first = factory.identity()
    second = factory.identity()

    from clinic_api.db.session import tenant_session

    with tenant_session(runtime_engine, first) as session:
        assert (
            session.execute(
                text("SELECT id FROM tenants WHERE id = :tenant"),
                {"tenant": second.tenant_id},
            ).all()
            == []
        )
        with pytest.raises(ProgrammingError):
            session.execute(
                text("UPDATE tenants SET name = 'Denied' WHERE id = :tenant"),
                {"tenant": second.tenant_id},
            )


def test_pool_context_reset_after_exception(factory, runtime_engine: Engine) -> None:
    first = factory.identity()
    second = factory.identity()
    engine = create_engine(
        runtime_engine.url.render_as_string(hide_password=False),
        pool_size=1,
        max_overflow=0,
    )

    from clinic_api.db.session import tenant_session

    try:
        with pytest.raises(RuntimeError), tenant_session(engine, first):
            raise RuntimeError("abort tenant A")
        with tenant_session(engine, second) as session:
            assert (
                session.scalar(
                    text("SELECT count(*) FROM tenants WHERE id = :tenant"),
                    {"tenant": first.tenant_id},
                )
                == 0
            )
            assert (
                session.scalar(
                    text("SELECT count(*) FROM tenants WHERE id = :tenant"),
                    {"tenant": second.tenant_id},
                )
                == 1
            )
    finally:
        engine.dispose()


def test_missing_context_sees_no_business_rows(factory, runtime_engine: Engine) -> None:
    factory.identity()
    with runtime_engine.connect() as connection:
        assert connection.execute(text("SELECT id FROM tenants")).all() == []


def test_inactive_membership_is_denied(factory, runtime_engine: Engine) -> None:
    from clinic_api.domain.shared.errors import AccessDenied

    context = factory.identity()
    factory.deactivate_membership(context.tenant_id, context.user_id)

    from clinic_api.db.session import tenant_session

    with pytest.raises(AccessDenied), tenant_session(runtime_engine, context):
        pass
