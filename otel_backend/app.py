from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from otel_backend import logger
from otel_backend.deserializers import deserialize_logs
from otel_backend.deserializers import deserialize_metrics
from otel_backend.deserializers import deserialize_trace
from otel_backend.models import LogsResponse
from otel_backend.models import MetricsResponse
from otel_backend.models import TraceResponse
from otel_backend.store import STORE
from otel_backend.store import add_logs_to_store
from otel_backend.store import add_metrics_to_store
from otel_backend.store import add_trace_to_store


app = FastAPI()


@app.post("/v1/traces", response_model=TraceResponse)
async def receive_traces(request: Request) -> TraceResponse:
    logger.info(f"Received request: {await request.body()}")
    try:
        raw_data = await request.body()
        trace = await deserialize_trace(raw_data)
        await add_trace_to_store(trace)
        logger.info(f"Received Trace: {trace}")
        return TraceResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/metrics", response_model=MetricsResponse)
async def receive_metrics(request: Request) -> MetricsResponse:
    try:
        raw_data = await request.body()
        metrics = await deserialize_metrics(raw_data)
        await add_metrics_to_store(metrics)
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
        await add_logs_to_store(logs)
        logger.info(f"Received Logs: {logs}")
        return LogsResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/store/traces")
async def get_traces() -> list:
    return STORE['traces']


@app.get("/store/metrics")
async def get_metrics() -> list:
    return STORE['metrics']


@app.get("/store/logs")
async def get_logs() -> list:
    return STORE['logs']


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
