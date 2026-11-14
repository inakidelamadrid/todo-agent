"""App factory. Builds the FastAPI application and mounts routers.

Settings are resolved here so that misconfiguration (missing/empty
``API_KEYS``) fails at startup instead of serving unauthenticated traffic.

Protected by default: every non-public router must be mounted with
``dependencies=[Depends(require_api_key)]``.
"""

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

from app.routes import public
from app.security import API_KEY_HEADER_NAME
from app.settings import get_settings


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
        return schema

    return _custom_openapi


def create_app() -> FastAPI:
    settings = get_settings()  # raises at startup when API_KEYS is missing/empty

    app = FastAPI(title="todo-agent API", version=settings.app_version)
    app.openapi = _openapi_with_api_key_scheme(app)  # type: ignore[method-assign]
    app.include_router(public.router)
    # Mount future routers here with:
    #   app.include_router(some_router, dependencies=[Depends(require_api_key)])
    return app


app = create_app()
