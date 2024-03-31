from otel_backend.ml.extract import extract_data
from pathlib import Path
import json
import pytest


@pytest.mark.asyncio
async def test_unpacked_data_can_be_extracted():
    current_file_path = Path(__file__)
    project_root = current_file_path.parent.parent
    json_file_path = project_root / 'tests' / 'assets' / 'unpacked_data.json'
    with json_file_path.open('r') as f:
        data = json.load(f)

    extracted_data = await extract_data(data)
    assert extracted_data[0].get('ip_source') == '10.0.1.170'
