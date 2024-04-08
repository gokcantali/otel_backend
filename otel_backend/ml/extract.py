from dataclasses import dataclass, field
from typing import List

from otel_backend.ml import logger


@dataclass
class TraceLabels:
    pod_label: str = ""
    namespace_label: str = ""
    source_port_label: str = ""
    destination_port_label: str = ""
    ack_flag: str = ""
    psh_flag: bool = False


@dataclass
class Trace:
    ip_source: str = ""
    ip_destination: str = ""
    labels: TraceLabels = field(default_factory=TraceLabels)


async def extract_data(trace) -> List[Trace]:
    data = trace.get("resourceSpans", [])
    extracted_info: List[Trace] = []
    for item in data:
        trace_instance = Trace()
        try:
            for attribute in item["resource"]["attributes"]:
                if attribute["key"] == "k8s.namespace.name":
                    trace_instance.labels.namespace_label = attribute["value"][
                        "stringValue"
                    ]
                elif attribute["key"] == "k8s.pod.name":
                    trace_instance.labels.pod_label = attribute["value"]["stringValue"]

            for scopeSpan in item["scopeSpans"]:
                for span in scopeSpan["spans"]:
                    for attribute in span["attributes"]:
                        if attribute["key"] == "cilium.flow_event.IP.source":
                            trace_instance.ip_source = attribute["value"]["stringValue"]
                        elif attribute["key"] == "cilium.flow_event.IP.destination":
                            trace_instance.ip_destination = attribute["value"][
                                "stringValue"
                            ]
                        elif attribute["key"] == "cilium.flow_event.l4.TCP.source_port":
                            trace_instance.labels.source_port_label = attribute[
                                "value"
                            ]["stringValue"]
                        elif (
                            attribute["key"]
                            == "cilium.flow_event.l4.TCP.destination_port"
                        ):
                            trace_instance.labels.destination_port_label = attribute[
                                "value"
                            ]["stringValue"]
                        elif attribute["key"] == "cilium.flow_event.l4.TCP.flags.ACK":
                            trace_instance.labels.ack_flag = attribute["value"][
                                "stringValue"
                            ]
                        elif attribute["key"] == "cilium.flow_event.l4.TCP.flags.PSH":
                            trace_instance.labels.psh_flag = (
                                attribute["value"]["stringValue"] == "true"
                            )
            extracted_info.append(trace_instance)
        except KeyError as e:
            logger.error(f"Key error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
    return extracted_info
