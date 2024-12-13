import io
import os
import zipfile
from typing import List

import pytest
from fastapi import Response

from otel_backend.csv import get_csv_response, save_csv
from otel_backend.extract import Trace, TraceLabels


def load_trace_data(json_data: List[dict]) -> List[Trace]:
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
            labels=labels,
            timestamp=item.get('timestamp', "")
        )
        traces.append(trace)
    return traces

@pytest.mark.asyncio
async def test_save_csv():
    json_data = [
        {
            "ip_source": "192.168.1.1",
            "ip_destination": "10.0.0.1",
            "is_anomaly": True,
            "labels": {
                "source_pod_label": "pod1",
                "source_namespace_label": "ns1",
                "source_port_label": "port1",
                "destination_pod_label": "pod2",
                "destination_namespace_label": "ns2",
                "destination_port_label": "port2",
                "ack_flag": True,
                "psh_flag": False
            },
            "timestamp": "2023-01-01T12:00:00Z"
        }
    ]
    traces = load_trace_data(json_data)
    save_csv(traces)

    file_path = './data/traces.csv'
    assert os.path.exists(file_path), "CSV file was not created."

    with open(file_path, 'r') as f:
        content = f.read()
        assert "ip_source,ip_destination,is_anomaly,source_pod_label,source_namespace_label,source_port_label,destination_pod_label,destination_namespace_label,destination_port_label,ack_flag,psh_flag,timestamp" in content
        assert "192.168.1.1,10.0.0.1,True,pod1,ns1,port1,pod2,ns2,port2,True,False,2023-01-01T12:00:00Z" in content

    # Test appending data
    json_data_append = [
        {
            "ip_source": "192.168.1.2",
            "ip_destination": "10.0.0.2",
            "is_anomaly": False,
            "labels": {
                "source_pod_label": "pod3",
                "source_namespace_label": "ns3",
                "source_port_label": "port3",
                "destination_pod_label": "pod4",
                "destination_namespace_label": "ns4",
                "destination_port_label": "port4",
                "ack_flag": False,
                "psh_flag": True
            },
            "timestamp": "2023-01-02T12:00:00Z"
        }
    ]
    traces_append = load_trace_data(json_data_append)
    save_csv(traces_append)

    with open(file_path, 'r') as f:
        content = f.read()
        assert "192.168.1.2,10.0.0.2,False,pod3,ns3,port3,pod4,ns4,port4,False,True,2023-01-02T12:00:00Z" in content

    # Cleanup
    os.remove(file_path)

@pytest.mark.asyncio
async def test_get_csv():
    json_data = [
        {
            "ip_source": "192.168.1.1",
            "ip_destination": "10.0.0.1",
            "is_anomaly": True,
            "labels": {
                "source_pod_label": "pod1",
                "source_namespace_label": "ns1",
                "source_port_label": "port1",
                "destination_pod_label": "pod2",
                "destination_namespace_label": "ns2",
                "destination_port_label": "port2",
                "ack_flag": True,
                "psh_flag": False
            },
            "timestamp": "2023-01-01T12:00:00Z"
        }
    ]
    traces = load_trace_data(json_data)
    save_csv(traces)

    response = Response()
    response = await get_csv_response(set_header=True)
    
    assert response.body is not None, "No content returned from get_csv."
    assert "Content-Disposition" in response.headers, "Content-Disposition header not set."
    assert "Content-Type" in response.headers, "Content-Type header not set."
    assert response.headers["Content-Disposition"] == "attachment; filename=traces.zip"
    assert response.headers["Content-Type"] == "application/zip"
    
    zip_buffer = io.BytesIO(response.body)
    with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
        with zip_file.open("traces.csv") as f:
            content = f.read().decode()
            assert "ip_source,ip_destination,is_anomaly,source_pod_label,source_namespace_label,source_port_label,destination_pod_label,destination_namespace_label,destination_port_label,ack_flag,psh_flag,timestamp" in content
            assert "192.168.1.1,10.0.0.1,True,pod1,ns1,port1,pod2,ns2,port2,True,False,2023-01-01T12:00:00Z" in content

    # Cleanup
    file_path = './data/traces.csv'
    os.remove(file_path)
