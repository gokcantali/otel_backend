from typing import List

from fastapi import FastAPI, HTTPException, Request

from otel_backend import logger
from otel_backend.deserializers import (
    deserialize_logs,
    deserialize_metrics,
    deserialize_trace,
)
from otel_backend.ml.extract import Trace, extract_data
from otel_backend.ml.model import get_model
from otel_backend.models import LogsResponse, MetricsResponse, TraceResponse
from torch.types import Number

TRACES: List[Trace] = []

app = FastAPI()


@app.post("/v1/traces", response_model=TraceResponse)
async def receive_traces(request: Request) -> TraceResponse:
    global TRACES
    raw_data = await request.body()
    trace = None
    extracted_traces = []
    try:
        trace = await deserialize_trace(raw_data)
        extracted_traces = await extract_data(trace)
        TRACES = extracted_traces
        model = get_model()
        for extracted_trace in extracted_traces:
            model.train(extracted_trace)
        return TraceResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail="Error processing request")


@app.post("/v1/metrics", response_model=MetricsResponse)
async def receive_metrics(request: Request) -> MetricsResponse:
    try:
        raw_data = await request.body()
        metrics = await deserialize_metrics(raw_data)
        logger.info(f"Received Metrics: {metrics}")
        return MetricsResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/logs", response_model=LogsResponse)
async def receive_logs(request: Request) -> LogsResponse:
    try:
        raw_data = await request.body()
        logs = await deserialize_logs(raw_data)
        logger.info(f"Received Logs: {logs}")
        return LogsResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/traces", response_model=List[Trace])
async def get_traces():
    return TRACES


@app.post("/predict", response_model=Number)
async def predict(trace: Trace):
    model = get_model()
    anomaly_prediction = model.predict(trace)
    return anomaly_prediction


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
