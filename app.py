from flask import Flask
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource, SERVICE_INSTANCE_ID

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

import logging
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
import json
import os
from random import randint
from flask import Flask, request

resource = Resource.create(
    attributes={
        SERVICE_NAME: "some-service",
        SERVICE_INSTANCE_ID: "some-instance-id",
    }
    )


# Configure traces
# resource = Resource(attributes={SERVICE_NAME: "flask-otel-logger"})
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# Configure logs
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)
log_exporter = OTLPLogExporter(endpoint="http://127.0.0.1:4317/v1/logs")
logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
# logger_provider.add_log_processor(BatchLogRecordProcessor(log_exporter))
handler = LoggingHandler(level=logging.DEBUG,logger_provider=logger_provider)
logger = logging.getLogger("example_logger")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Configure metrics
exporter = OTLPMetricExporter(endpoint="http://localhost:4318/v1/metrics")
reader = PeriodicExportingMetricReader(exporter)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter("flask_app_meter")

# Create request counter
request_counter = meter.create_counter(
    name="app_requests_counter",
    description="Counts total app requests"
)

app = Flask(__name__)
app.logger.addHandler(handler)

tracer = trace.get_tracer(__name__)

@app.route('/')
def hello_world():
    request_counter.add(1)
    logger.info(
        "LOG SAYS HELLO",
        extra={"method": "GET", "status": 200, "level": "info"}
    )
    with tracer.start_as_current_span("some_span"):
        app.logger.info("TRACING SAYS HELLO")
        return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
