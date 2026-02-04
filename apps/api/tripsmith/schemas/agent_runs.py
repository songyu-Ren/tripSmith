from __future__ import annotations

import datetime as dt

from pydantic import BaseModel
from pydantic import ConfigDict


class AgentRunDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    trip_id: str
    created_at: dt.datetime
    phase: str
    input_json: dict
    output_json: dict
    tool_calls_json: list
    model_info: dict
    prompt_version: str
    commit_hash: str


class AgentRunListResponse(BaseModel):
    runs: list[AgentRunDto]

