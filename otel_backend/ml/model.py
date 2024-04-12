import torch
from torch.nn import functional as F
from torch.types import Number

from otel_backend.ml import NODE_EMBEDDING_SIZE, logger
from otel_backend.ml.extract import Trace
from otel_backend.ml.gat_net import GATNet

MODEL = None

class GATNetWrapper:
    """
    A wrapper class for managing the GATNet model. It facilitates the training process and prediction generation.
    
    Attributes:
        model (GATNet): The GATNet model instance.
        optimizer (torch.optim.Adam): The optimizer for training the GATNet model.
    """
    def __init__(self) -> None:
        """
        Initializes the GATNet model and its optimizer.
        """
        self.model = GATNet(num_node_features=NODE_EMBEDDING_SIZE, num_edge_features=2, num_classes=2)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01, weight_decay=5e-4)

    def train(self, trace: Trace) -> tuple[Number, Number]:
        """
        Trains the GATNet model on a single batch of traces and returns the anomaly probability for the currently added edge.

        Parameters:
            trace (Trace): A single trace object to be processed and trained on.

        Returns:
            loss (float): The loss value computed for the batch of traces.
            anomaly_prob (float): The anomaly probability for the currently added edge.
        """
        data = self.model.preprocess_traces(trace)
        self.model.train()
        self.optimizer.zero_grad()
        out = self.model(data.x, data.edge_index, data.edge_attr)

        # Hypothetical example with is a list of integers
        # 0/1 representing the true class of each node
        if trace.is_anomaly:
            target = torch.tensor([1, 1], dtype=torch.long)
        else:
            target = torch.tensor([0, 0], dtype=torch.long)

        loss = F.nll_loss(out, target)
        loss.backward()
        self.optimizer.step()

        anomaly_prob = torch.softmax(out, dim=1)[-1][1].item()

        logger.info(f"Anomaly Probability: {anomaly_prob} | Loss: {loss.item()}")

        return loss.item(), anomaly_prob

def get_model() -> GATNetWrapper:
    """
    Returns a singleton instance of the GATNetWrapper class.

    Returns:
        GATNetWrapper: The singleton instance of GATNetWrapper.
    """
    global MODEL
    if MODEL is None:
        MODEL = GATNetWrapper()
    return MODEL
