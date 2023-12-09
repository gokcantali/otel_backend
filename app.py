from flask import Flask
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Configure traces
resource = Resource(attributes={SERVICE_NAME: "flask-otel-logger"})
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

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

tracer = trace.get_tracer(__name__)

@app.route('/')
def hello_world():
    request_counter.add(1)
    with tracer.start_as_current_span("hello-world"):
        app.logger.info("Hello, world! Received a request.")
        return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
