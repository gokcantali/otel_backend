from gzip import GzipFile
from io import BytesIO

from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.logs.v1 import logs_service_pb2
from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2

from otel_backend import logger


async def deserialize_trace(data: bytes) -> dict:
    try:
        with GzipFile(fileobj=BytesIO(data), mode="rb") as f:
            decompressed_data = f.read()
    except IOError:
        decompressed_data = data
    try:
        trace = trace_service_pb2.ExportTraceServiceRequest()
        trace.ParseFromString(decompressed_data)
        return MessageToDict(trace)
    except Exception as e:
        logger.error(f"Error parsing trace data: {e}")
        raise


async def deserialize_metrics(data: bytes) -> dict:
    try:
        with GzipFile(fileobj=BytesIO(data), mode="rb") as f:
            decompressed_data = f.read()
    except IOError:
        decompressed_data = data
    try:
        metrics = metrics_service_pb2.ExportMetricsServiceRequest()
        metrics.ParseFromString(decompressed_data)
        return MessageToDict(metrics)
    except Exception as e:
        logger.error(f"Error parsing metrics data: {e}")
        raise


async def deserialize_logs(data: bytes) -> dict:
    try:
        with GzipFile(fileobj=BytesIO(data), mode="rb") as f:
            decompressed_data = f.read()
    except IOError:
        decompressed_data = data
    try:
        logs = logs_service_pb2.ExportLogsServiceRequest()
        logs.ParseFromString(decompressed_data)
        return MessageToDict(logs)
    except Exception as e:
        logger.error(f"Error parsing logs data: {e}")
        raise
