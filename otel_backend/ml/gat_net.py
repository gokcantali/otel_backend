from collections import defaultdict
from torch_geometric.data import Data
from torch_geometric.nn import GATConv
import numpy as np
import torch
import torch.nn.functional as F

from otel_backend.ml.extract import Trace


class LabelEmbeddings:
    def __init__(self, embedding_dim=16):
        self.pod_embeddings = torch.nn.Embedding(num_embeddings=1000, embedding_dim=embedding_dim)
        self.namespace_embeddings = torch.nn.Embedding(num_embeddings=1000, embedding_dim=embedding_dim)
        self.pod_label_to_index = {}
        self.namespace_label_to_index = {}
        self.pod_counter = 0
        self.namespace_counter = 0

    def get_pod_embedding(self, pod_label):
        if pod_label not in self.pod_label_to_index:
            self.pod_label_to_index[pod_label] = self.pod_counter
            self.pod_counter += 1
        return self.pod_embeddings(torch.tensor([self.pod_label_to_index[pod_label]], dtype=torch.long))

    def get_namespace_embedding(self, namespace_label):
        if namespace_label not in self.namespace_label_to_index:
            self.namespace_label_to_index[namespace_label] = self.namespace_counter
            self.namespace_counter += 1
        return self.namespace_embeddings(torch.tensor([self.namespace_label_to_index[namespace_label]], dtype=torch.long))


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

        self.pod_label_encoder = {}
        self.namespace_label_encoder = {}

        self.label_embeddings = LabelEmbeddings()
        
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

    def encode_label(self, label, encoder):
        """
        Dynamically encodes a label, adding it to the encoder if not present.

        Parameters:
            label (str): The label to encode.
            encoder (dict): The encoder dictionary.

        Returns:
            int: The encoded label.
        """
        if label not in encoder:
            encoder[label] = len(encoder)
        return encoder[label]

    def preprocess_traces(self, trace: Trace):
        """
        Processes a single trace object, encoding features dynamically and
        preparing data for the GATNet model. Utilizes embeddings for
        pod and namespace labels.

        Parameters:
            trace (Trace): A single trace object to be processed.

        Returns:
            Data: A PyTorch Geometric Data object with the processed graph.
        """
        node_features = defaultdict(lambda: np.zeros((36,)))  # Adjusted feature size

        edge_index = []
        edge_attr = []

        node_index = {}
        current_index = 0

        for ip, labels in [
                (trace.ip_source, trace.labels),
                (trace.ip_destination, trace.labels)
        ]:
            if ip not in node_index:
                node_index[ip] = current_index

                # Extract IP address features
                ip_features = [int(octet) for octet in ip.split('.')[:4]]

                # Get embeddings for pod and namespace labels
                pod_embedding = self.label_embeddings.get_pod_embedding(
                    labels.pod_label).detach().numpy()
                namespace_embedding = self.label_embeddings.get_namespace_embedding(
                    labels.namespace_label).detach().numpy()

                # Combine IP features with label embeddings
                combined_features = np.concatenate((
                    ip_features, pod_embedding.flatten(), namespace_embedding.flatten()))
                node_features[current_index] = combined_features

                current_index += 1

        # Ensure we only add valid edges
        if trace.ip_source in node_index and trace.ip_destination in node_index:
            source_idx = node_index[trace.ip_source]
            dest_idx = node_index[trace.ip_destination]
            edge_index.append([source_idx, dest_idx])

        # Convert dictionaries and lists to tensors for PyTorch Geometric
        x = torch.tensor(list(node_features.values()), dtype=torch.float)
        edge_index_tensor = (
            torch.tensor(edge_index, dtype=torch.long).t().contiguous()
            if edge_index
            else torch.empty((2, 0), dtype=torch.long))
        # Assuming edge_attr is properly handled elsewhere
        edge_attr_tensor = torch.tensor(edge_attr, dtype=torch.float)

        return Data(x=x, edge_index=edge_index_tensor, edge_attr=edge_attr_tensor)
