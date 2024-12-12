import json
from collections import OrderedDict
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from numpy import mean
from sklearn.metrics import accuracy_score
from torch_geometric.nn import GCNConv

from inference.preprocesser import preprocess_df, convert_to_graph


OPTIMIZER_STR_TO_OPTIMIZER = {
    "Adam": torch.optim.Adam,
    "AdamW": torch.optim.AdamW,
    "SGD": torch.optim.SGD,
    "LBFGS": torch.optim.LBFGS,
}


class GCN(torch.nn.Module):
    def __init__(
        self, optimizer_str, num_features, num_classes, weight_decay=1e-3, dropout=0.7,
        hidden_dim=16, epochs=30, lr=0.005, patience=3
    ):
        super(GCN, self).__init__()
        self.epochs = epochs
        self.patience = patience
        self.conv1 = GCNConv(num_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, num_classes)
        self.dropout = nn.Dropout(p=dropout)

        optimizer = OPTIMIZER_STR_TO_OPTIMIZER.get(optimizer_str, torch.optim.Adam)
        self.optimizer = optimizer(self.parameters(), lr=lr, weight_decay=weight_decay)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", factor=0.1, patience=self.patience, verbose=True
        )

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))

        x = F.relu(self.conv2(x, edge_index))
        x = self.dropout(x)

        x = self.conv3(x, edge_index)
        return F.log_softmax(x, dim=-1)

    def test_model(self, data):
        self.eval()
        out = self(data.x, data.edge_index)
        _, pred = out.max(dim=1)
        return pred

    def test_model_batch_mode(self, data):
        predictions = []
        losses = []
        labels = []
        for batch in data:
            labels += batch.y

            out = self(batch.x, batch.edge_index)
            loss = F.nll_loss(out, batch.y).item()
            losses.append(loss)
            _, pred = out.max(dim=1)
            predictions += pred

        accuracy = accuracy_score(predictions, labels)
        return predictions, mean(losses), accuracy

    def set_parameters(self, parameters: List[np.ndarray]):
        params_dict = zip(self.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.Tensor(v) for k, v in params_dict})
        self.load_state_dict(state_dict, strict=True)

    def get_parameters(self) -> List[np.ndarray]:
        return [val.cpu().numpy() for _, val in self.state_dict().items()]


def load_gcn_model_from_conf_file(conf_file_path: Path):
    # check if the configuration file exists
    if not conf_file_path or not conf_file_path.exists():
        return None

    # retrieve parameters from file to initialize GCN class instance
    conf = json.loads(open(conf_file_path, "r").read())

    pd_file_path = conf.pop("pd_file_path") # GCN pt file path
    gcn = GCN(**conf)  # initialize GCN class instance
    gcn.load_state_dict(torch.load(pd_file_path)) # load model parameters from pt file

    return gcn


def predict_trace_class(traces, gcn_conf_path="./gcn_conf.json"):
    # open result file for logging predictions
    result_file = open("results.txt", "a")

    gcn = load_gcn_model_from_conf_file(Path(gcn_conf_path))
    if gcn is None:
        result_file.write("No GCN model to be loaded!\n")
        return

    if len(traces) == 0:
        result_file.write("No traces to be predicted!\n")
        return

    # create DataFrame from traces
    traces_df = pd.DataFrame(traces)
    X, y = preprocess_df(traces_df, use_diversity_index=True)

    # construct graph data from DataFrame
    data = convert_to_graph(X, y)
    data.x[:, 18] = torch.zeros_like(data.x[:, 18])
    data.x[:, 19] = torch.zeros_like(data.x[:, 19])

    # predict trace class
    result_file.write("------Prediction starts-----\n")

    pred = gcn.test_model(data)
    for i in range(len(traces)):
        result_file.write(f"Trace {i} is predicted as {pred[i]}\n")

    result_file.write("------Prediction ends------\n")
    result_file.close()
