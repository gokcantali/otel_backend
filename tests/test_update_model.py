import json
from pathlib import Path
from typing import List

import pytest

from otel_backend.ml.extract import Trace, extract_data
from otel_backend.ml.model import get_model


@pytest.mark.asyncio
async def test_update_model_with_dataset():
    current_file_path = Path(__file__)
    project_root = current_file_path.parent.parent
    json_file_path = project_root / "tests" / "assets" / "data.json"
    with json_file_path.open("r") as f:
        data = json.load(f)

    extracted_traces: List[Trace] = []
    for trace in data:
        extracted_trace = await extract_data(trace)
        extracted_traces.extend(extracted_trace)

    losses = []
    for extracted_trace in extracted_traces:
        loss = get_model().train(extracted_trace)
        losses.append(loss)

    assert all(loss < 1 for loss in losses)
