import json
from pathlib import Path
from typing import List

import pytest

from otel_backend.ml.extract import Trace, TraceLabels, extract_data
from otel_backend.ml.model import get_model


def load_trace_data(json_data: str) -> List[Trace]:
    # Convert each item to a Trace instance
    traces = []
    for item in json_data:
        # Extract label data
        label_data = item.get('labels', {})
        labels = TraceLabels(
            source_pod_label=label_data.get('source_pod_label', ""),
            source_namespace_label=label_data.get('source_namespace_label', ""),
            source_port_label=label_data.get('source_port_label', ""),
            destination_pod_label=label_data.get('destination_pod_label', ""),
            destination_namespace_label=label_data.get('destination_namespace_label', ""),
            destination_port_label=label_data.get('destination_port_label', ""),
            ack_flag=label_data.get('ack_flag', False),
            psh_flag=label_data.get('psh_flag', False)
        )
        trace = Trace(
            ip_source=item.get('ip_source', ""),
            ip_destination=item.get('ip_destination', ""),
            is_anomaly=item.get('is_anomaly', False),
            labels=labels
        )
        traces.append(trace)
    return traces


@pytest.mark.asyncio
async def test_update_model_with_ipv6_data():
    current_file_path = Path(__file__)
    project_root = current_file_path.parent.parent
    json_file_path = project_root / "tests" / "assets" / "data_json_ipv6.json"
    with json_file_path.open("r") as f:
        data = json.load(f)

    extracted_traces = load_trace_data(data)
    for trace in data:
        extracted_trace = await extract_data(trace)
        extracted_traces.extend(extracted_trace)

    losses = []
    anomaly_probs = []
    for i, extracted_trace in enumerate(extracted_traces):
        loss, anomaly_prob = get_model().train(extracted_trace)
        losses.append(loss)
        anomaly_probs.append(anomaly_prob)
