"""App factory. Builds the FastAPI application and mounts routers.

Settings are resolved here so that misconfiguration (missing/empty
``API_KEYS``) fails at startup instead of serving unauthenticated traffic.

Protected by default: every non-public router must be mounted with
``dependencies=[Depends(require_principal)]`` (a person with a Clerk
session token or a machine with an API key).
"""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI

from app.bills.router import bills_router, payments_router
from app.db import build_engine, dispose_engine
from app.routes import me, public
from app.security import API_KEY_HEADER_NAME, require_principal, require_user
from app.settings import clerk_enabled, get_settings
from app.telegram.playground.router import playground_router
from app.telegram.webhook import telegram_webhook_router


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the DB engine once; dispose it on shutdown. Lazy: no
    connection is opened until a route actually needs the database."""
    engine = build_engine(get_settings())
    app.state.db_engine = engine
    try:
        yield
    finally:
        await dispose_engine(engine)


def _openapi_with_api_key_scheme(app: FastAPI) -> Callable[[], dict[str, Any]]:
    """Ensure the X-API-Key scheme always appears in the docs.

    FastAPI only adds a security scheme when a route uses it; the scheme
    must be visible even before the first protected router ships.
    """

    original_openapi = app.openapi

    def _custom_openapi() -> dict[str, Any]:
        schema = original_openapi()  # generates once, then returns the cached schema
        schemes = schema.setdefault("components", {}).setdefault("securitySchemes", {})
        schemes.setdefault(
            "APIKeyHeader",
            {"type": "apiKey", "in": "header", "name": API_KEY_HEADER_NAME},
        )
        schemes.setdefault(
            "BearerAuth",
            {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        )
        return schema

    return _custom_openapi


def create_app() -> FastAPI:
    settings = get_settings()  # raises at startup when API_KEYS is missing/empty
    if not clerk_enabled(settings):
        # Names the variables, never a value. api/.env holds the real ones.
        raise RuntimeError(
            "CLERK_JWT_PUBLIC_KEY, CLERK_AUTHORIZED_PARTIES and "
            "CLERK_ALLOWED_USER_IDS must all be set"
        )
    if settings.telegram_playground_enabled and settings.app_env == "production":
        # Names the variables, never a value.
        raise RuntimeError(
            "TELEGRAM_PLAYGROUND_ENABLED must be false when APP_ENV is production"
        )

    app = FastAPI(title="todo-agent API", version=settings.app_version, lifespan=_lifespan)
    app.openapi = _openapi_with_api_key_scheme(app)  # type: ignore[method-assign]
    app.include_router(public.router)
    # Public by ticket BE-008: guarded by the Telegram secret token, not an API key.
    app.include_router(telegram_webhook_router)
    # Protected by default: every business router accepts a person (Clerk
    # session) or a machine (API key) through one shared dependency.
    app.include_router(bills_router, dependencies=[Depends(require_principal)])
    app.include_router(payments_router, dependencies=[Depends(require_principal)])
    # A person, not a script: machines get 403 here (BE-064).
    app.include_router(me.router, dependencies=[Depends(require_user)])
    # Admin-only debugger playground, 404 when the switch is off (BE-068).
    app.include_router(playground_router)
    return app


app = create_app()
