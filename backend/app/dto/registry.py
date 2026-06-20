from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    instance_id: str
