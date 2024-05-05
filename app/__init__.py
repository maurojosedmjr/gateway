from typing import List
from pydantic import BaseModel, Field


class SubRoute(BaseModel):
    route: str
    is_public: bool = Field(False)


class Config(BaseModel):
    add_cors: bool = Field(True)
    sub_routes: List[SubRoute] = Field(default_factory=list)


class Endpoint(BaseModel):
    endpoint: str
    verbs: List[str]
    redirect_base: str = Field(..., description="Main url to redirect request")
    config: Config


class EndpointConfig(BaseModel):
    endpoint: str
    target_api: str
    verbs: List[str]
    is_public: bool = Field(False)
    public_variations: List[str] = Field(default_factory=list)
