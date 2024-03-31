from pathlib import Path
import json
import pytest

from otel_backend.ml.extract import extract_data
from otel_backend.ml.graph_model import get_graph_model


@pytest.mark.asyncio
async def test_unpacked_data_can_be_extracted():
    current_file_path = Path(__file__)
    project_root = current_file_path.parent.parent
    json_file_path = project_root / 'tests' / 'assets' / 'unpacked_data.json'
    with json_file_path.open('r') as f:
        data = json.load(f)

    graph = await get_graph_model()
    extracted_traces = await extract_data(data)
    out = []
    for extracted_trace in extracted_traces:
        anomaly_score, loss = await graph.train(extracted_trace)
        out.append((anomaly_score, loss))

    assert len(out) == 1
    assert isinstance(out[0][0], float)
    assert isinstance(out[0][1], float)
