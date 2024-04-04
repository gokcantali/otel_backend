from typing import List

import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GATConv

from otel_backend.ml.extract import Trace


class GATNet(torch.nn.Module):
    """
    Implements a Graph Attention Network (GAT) using PyTorch Geometric.
    This network is capable of processing graph-structured data by employing
    attention mechanisms over the edges of the graph.
    
    Attributes:
        conv1 (GATConv): The first GAT convolution layer.
        conv2 (GATConv): The second GAT convolution layer, producing the final output.
    """
    def __init__(self, num_node_features: int, num_edge_features: int, num_classes: int):
        """
        Initializes the GATNet model with specified sizes for the input features and the output classes.
        
        Parameters:
            num_node_features (int): Number of features for each node in the graph.
            num_edge_features (int): Number of features for each edge in the graph. Currently not directly used but included for future extensions.
            num_classes (int): Number of classes for the classification task.
        """
        super(GATNet, self).__init__()
        self.conv1 = GATConv(num_node_features, 8, add_self_loops=False)
        self.conv2 = GATConv(8, num_classes, add_self_loops=False)
        
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor = None) -> torch.Tensor:
        """
        Defines the forward pass of the GAT network.
        
        Parameters:
            x (torch.Tensor): Node feature matrix of shape [num_nodes, num_node_features].
            edge_index (torch.Tensor): Graph connectivity in COO format with shape [2, num_edges].
            edge_attr (torch.Tensor, optional): Edge attribute matrix of shape [num_edges, num_edge_features].
        
        Returns:
            torch.Tensor: The log softmax output of the second convolutional layer.
        """
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, training=self.training)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)

def preprocess_traces(traces: List[Trace]) -> Data:
    """
    Processes a list of Trace objects into a PyTorch Geometric Data object suitable
    for GAT model input.
    
    Parameters:
        traces (List[Trace]): A list of Trace dataclass instances to be processed.
    
    Returns:
        Data: A PyTorch Geometric Data object containing the processed graph data.
    """
    edge_index = []
    edge_attr = []

    node_index = {}
    current_index = 0

    for trace in traces:
        if trace.ip_source not in node_index:
            node_index[trace.ip_source] = current_index
            current_index += 1
        if trace.ip_destination not in node_index:
            node_index[trace.ip_destination] = current_index
            current_index += 1

        source_idx = node_index[trace.ip_source]
        dest_idx = node_index[trace.ip_destination]
        
        edge_index.append([source_idx, dest_idx])

        edge_features = [
            int(trace.labels.ack_flag == 'true'),
            trace.labels.psh_flag
        ]
        edge_attr.append(edge_features)

    num_nodes = current_index
    x = torch.eye(num_nodes)
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_attr, dtype=torch.float)

    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
