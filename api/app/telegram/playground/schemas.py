"""Request and response bodies for the playground tools (BE-078).

Limits live here, so an oversized body is a 422 before any route code runs.
Template data is never stored or logged.
"""

from collections.abc import Mapping
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

DataKey = Annotated[str, StringConstraints(min_length=1, max_length=40)]
DataValue = Annotated[str, StringConstraints(max_length=1000)]


class TemplateRequest(BaseModel):
    """A template and its sample data. Unknown fields are rejected: there is
    no way to smuggle in a recipient or raw text."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    template: str = Field(min_length=1, max_length=64)
    data: Mapping[DataKey, DataValue] = Field(default_factory=dict, max_length=20)


class TemplateEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    fields: tuple[str, ...]


class TemplateList(BaseModel):
    model_config = ConfigDict(frozen=True)

    templates: tuple[TemplateEntry, ...]


class TemplatePreview(BaseModel):
    """Exactly the text Telegram would receive, and its length."""

    model_config = ConfigDict(frozen=True)

    html: str
    length: int
