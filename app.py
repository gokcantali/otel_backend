from flask import Flask
import logging
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_INSTANCE_ID
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry._logs import set_logger_provider

OTLP_ENDPOINT = "http://127.0.0.1"

def configure_resource():
    """Configure and return a resource with service name and instance ID."""
    return Resource.create(attributes={
        SERVICE_NAME: "some-service",
        SERVICE_INSTANCE_ID: "some-instance-id",
    })

def configure_tracing(resource):
    """Configure and set tracer provider."""
    trace.set_tracer_provider(TracerProvider(resource=resource))
    otlp_exporter = OTLPSpanExporter(endpoint=f"{OTLP_ENDPOINT}:4318/v1/traces")
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

def configure_logging(resource):
    """Configure and set logging."""
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    log_exporter = OTLPLogExporter(endpoint=f"{OTLP_ENDPOINT}:4317/v1/logs")
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    handler = LoggingHandler(level=logging.DEBUG, logger_provider=logger_provider)
    logger = logging.getLogger("example_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return handler

def configure_metrics():
    """Configure and return a meter for metrics."""
    exporter = OTLPMetricExporter(endpoint=f"{OTLP_ENDPOINT}:4318/v1/metrics")
    reader = PeriodicExportingMetricReader(exporter)
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    return metrics.get_meter("flask_app_meter")

resource = configure_resource()
configure_tracing(resource)
log_handler = configure_logging(resource)
meter = configure_metrics()

app = Flask(__name__)
app.logger.addHandler(log_handler)

tracer = trace.get_tracer(__name__)

@app.route('/')
def hello_world():
    request_counter = meter.create_counter(
        name="app_requests_counter",
        description="Counts total app requests"
    )
    request_counter.add(1)
    logger = logging.getLogger("example_logger")
    logger.info(
        "LOG SAYS HELLO",
        extra={"method": "GET", "status": 200, "level": "info"}
    )
    with tracer.start_as_current_span("some_span"):
        app.logger.info("TRACING SAYS HELLO")
        return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
