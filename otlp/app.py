from fastapi import FastAPI, Request, HTTPException
from otlp.models import TraceResponse, MetricsResponse
from otlp.deserializers import deserialize_trace, deserialize_metrics
from otlp import logger


app = FastAPI()


@app.post("/v1/traces", response_model=TraceResponse)
async def receive_traces(request: Request) -> TraceResponse:
    try:
        raw_data = await request.body()
        trace = deserialize_trace(raw_data)
        logger.info(f"Received Trace: {trace}")
        return TraceResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/metrics", response_model=MetricsResponse)
async def receive_metrics(request: Request) -> MetricsResponse:
    try:
        raw_data = await request.body()
        metrics = deserialize_metrics(raw_data)
        logger.info(f"Received Metrics: {metrics}")
        return MetricsResponse(status="received")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
