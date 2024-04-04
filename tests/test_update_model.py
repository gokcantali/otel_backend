import json
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
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
    anomaly_probs = []
    for extracted_trace in extracted_traces:
        loss, anomaly_prob = get_model().train(extracted_trace)
        losses.append(loss)
        anomaly_probs.append(anomaly_prob)

    plt.figure(figsize=(10, 5))
    plt.plot(losses, label='Training Loss')
    plt.xlabel('Iteration')
    plt.ylabel('Loss')
    plt.title('Training Loss Over Time')
    plt.legend()
    plot_save_path = project_root / "tests" / "assets" / "training_loss_plot.png"
    plt.savefig(plot_save_path)

    plt.figure(figsize=(10, 5))
    plt.plot(anomaly_probs, label='Anomaly Probability')
    plt.xlabel('Iteration')
    plt.ylabel('Anomaly Probability')
    plt.title('Anomaly Probability Over Time')
    plt.legend()
    plot_save_path = project_root / "tests" / "assets" / "anomaly_probability_plot.png"
    plt.savefig(plot_save_path)
