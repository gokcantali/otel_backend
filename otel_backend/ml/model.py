import torch
from torch.nn import functional as F

from otel_backend.ml.extract import Trace
from otel_backend.ml.gat_net import GATNet, preprocess_traces

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
        self.model = GATNet(num_node_features=2, num_edge_features=2, num_classes=2)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01, weight_decay=5e-4)

    def train(self, trace: Trace) -> float:
        """
        Trains the GATNet model on a single batch of traces.
        
        Parameters:
            trace (Data): A PyTorch Geometric Data object representing a single trace or a batch of traces.
        
        Returns:
            float: The loss value computed for the batch of traces.
        """
        data = preprocess_traces([trace])
        self.model.train()
        self.optimizer.zero_grad()
        out = self.model(data.x, data.edge_index, data.edge_attr)
        target = torch.tensor([0] * data.num_nodes, dtype=torch.long)  # Placeholder for actual targets
        loss = F.nll_loss(out, target)
        loss.backward()
        self.optimizer.step()
        return loss.item()

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
