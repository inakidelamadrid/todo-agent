"""GET /me: who is the signed-in caller (BE-064, roles BE-067).

Proves the API accepts the web app's session; also the reference route for
``require_user`` ('a person, not a script'). No profile data, no database.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.principal import Principal, User, is_admin
from app.security import require_principal
from app.settings import Settings, get_settings, parse_admin_user_ids

router = APIRouter(tags=["me"])


class MeResponse(BaseModel):
    """Same camelCase-on-the-wire config as bills' model (copied, per ticket)."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, frozen=True
    )

    user_id: str
    kind: Literal["user"] = "user"
    roles: tuple[Literal["admin"], ...] = ()


@router.get("/me", response_model=MeResponse, summary="Identify the signed-in user")
def me(
    principal: Annotated[Principal, Depends(require_principal)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MeResponse:
    # The router is mounted behind require_user (403 for machines), so the
    # only check of 'a person is required' stays in that dependency.
    assert isinstance(principal, User)
    roles: tuple[Literal["admin"], ...] = (
        ("admin",)
        if is_admin(principal, parse_admin_user_ids(settings.admin_user_ids))
        else ()
    )
    return MeResponse(user_id=principal.user_id, roles=roles)
