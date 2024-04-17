import csv
import io
import zipfile
from typing import List

from fastapi import FastAPI, HTTPException, Request, Response
from torch.types import Number

from otel_backend import logger
from otel_backend.deserializers import (
    deserialize_logs,
    deserialize_metrics,
    deserialize_trace,
)
from otel_backend.ml.extract import Trace, extract_data
from otel_backend.ml.model import get_model
from otel_backend.models import LogsResponse, MetricsResponse, TraceResponse

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
        TRACES.extend(extracted_traces)
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

@app.get("/traces.csv")
@app.get("/traces.csv")
async def get_traces_csv(response: Response):
    # Create a CSV string
    csv_data = io.StringIO()
    csv_writer = csv.writer(csv_data)
    csv_writer.writerow(['ip_source', 'ip_destination', 'is_anomaly',
                         'source_pod_label', 'source_namespace_label', 'source_port_label',
                         'destination_pod_label', 'destination_namespace_label', 'destination_port_label',
                         'ack_flag', 'psh_flag'])
    for trace in TRACES:
        csv_writer.writerow([
            trace.ip_source.encode('utf-8'),
            trace.ip_destination.encode('utf-8'),
            trace.is_anomaly,
            trace.labels.source_pod_label.encode('utf-8'),
            trace.labels.source_namespace_label.encode('utf-8'),
            trace.labels.source_port_label.encode('utf-8'),
            trace.labels.destination_pod_label.encode('utf-8'),
            trace.labels.destination_namespace_label.encode('utf-8'),
            trace.labels.destination_port_label.encode('utf-8'),
            trace.labels.ack_flag,
            trace.labels.psh_flag
        ])

    # Create a zip file containing the CSV
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("traces.csv", csv_data.getvalue())

    # Set response headers for download
    response.headers["Content-Disposition"] = "attachment; filename=traces.zip"
    response.headers["Content-Type"] = "application/zip"

    # Return the zip file as a response
    return zip_buffer.getvalue()

@app.post("/predict", response_model=Number)
async def predict(trace: Trace):
    model = get_model()
    anomaly_prediction = model.predict(trace)
    return anomaly_prediction


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
