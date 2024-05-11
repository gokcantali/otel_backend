from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response

from otel_backend import logger
from otel_backend.csv import get_csv_response, save_csv
from otel_backend.deserializers import (
    deserialize_logs,
    deserialize_metrics,
    deserialize_traces,
)
from otel_backend.extract import extract_data
from otel_backend.models import LogsResponse, MetricsResponse, TraceResponse

app = FastAPI()


async def process_traces(raw_data: bytes):
    trace = None
    extracted_traces = []
    try:
        traces = await deserialize_traces(raw_data)
        logger.info(f"Received Traces: {len(traces)}")
    except Exception as e:
        logger.error(f"Error deserializing traces: {e}")
    try:
        extracted_traces = await extract_data(trace)
        logger.info(f"Extracted Traces: {len(extracted_traces)}")
    except Exception as e:
        logger.error(f"Error extracting traces: {e}")
    try:
        await save_csv(extracted_traces)
    except Exception as e:
        logger.error(f"Error saving traces: {e}")

@app.post("/v1/traces", response_model=TraceResponse)
async def receive_traces(request: Request, background_tasks: BackgroundTasks) -> TraceResponse:
    raw_data = await request.body()
    background_tasks.add_task(process_traces, raw_data)
    return TraceResponse(status="received")

@app.post("/v1/metrics", response_model=MetricsResponse)
async def receive_metrics(request: Request) -> MetricsResponse:
    try:
        raw_data = await request.body()
        metrics = await deserialize_metrics(raw_data)
        logger.info(f"Received Metrics: {len(metrics)}")
        return MetricsResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/v1/logs", response_model=LogsResponse)
async def receive_logs(request: Request) -> LogsResponse:
    try:
        raw_data = await request.body()
        logs = await deserialize_logs(raw_data)
        logger.info(f"Received Logs: {len(logs)}")
        return LogsResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/traces.zip")
async def get_traces_csv(response: Response):
    try:
        response = await get_csv_response()
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return response

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
