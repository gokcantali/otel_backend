from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request

from otel_backend import logger
from otel_backend.deserializers import deserialize_logs
from otel_backend.deserializers import deserialize_metrics
from otel_backend.deserializers import deserialize_trace
from otel_backend.ml.graph_model import get_graph_model
from otel_backend.models import LogsResponse
from otel_backend.models import MetricsResponse
from otel_backend.models import TraceResponse
from otel_backend.ml.extract import extract_data


app = FastAPI()


@app.post("/v1/traces", response_model=TraceResponse)
async def receive_traces(request: Request) -> TraceResponse:
    try:
        raw_data = await request.body()
        trace = await deserialize_trace(raw_data)
        graph = await get_graph_model()
        extracted_traces = await extract_data(trace)
        for extracted_trace in extracted_traces:
            await graph.train(extracted_trace)
        return TraceResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
