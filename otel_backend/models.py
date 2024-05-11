from pydantic import BaseModel


class TraceResponse(BaseModel):
    status: str


class MetricsResponse(BaseModel):
    status: str


class LogsResponse(BaseModel):
    status: str
