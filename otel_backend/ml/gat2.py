import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GATConv

from otel_backend.ml.extract import Trace
from otel_backend.ml import NODE_EMBEDDING_SIZE

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
    def __init__(self, num_node_features: int, num_edge_features: int, num_classes: int):
        super(GATNet, self).__init__()
        self.conv1 = GATConv(num_node_features, 8, add_self_loops=False)
        self.conv2 = GATConv(8, num_classes, add_self_loops=False)
        self.label_embeddings = LabelEmbeddings()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor = None) -> torch.Tensor:
        x = F.relu(self.conv1(x, edge_index, edge_attr))
        x = F.dropout(x, training=self.training)
        x = self.conv2(x, edge_index, edge_attr)
        return F.log_softmax(x, dim=1)

    def preprocess_traces(self, trace: Trace):
        node_features = []
        edge_index = []
        edge_attr = []  # List to store edge attributes
        node_index = {}

        # Extract IP address features
        source_ip_features = np.array([int(octet) for octet in trace.ip_source.split('.')], dtype=np.float32)
        destination_ip_features = np.array([int(octet) for octet in trace.ip_destination.split('.')], dtype=np.float32)

        # Get embeddings for pod and namespace labels
        source_pod_embedding = self.label_embeddings.get_pod_embedding(
            trace.labels.source_pod_label).detach().numpy().flatten()
        source_namespace_embedding = self.label_embeddings.get_namespace_embedding(
            trace.labels.source_namespace_label).detach().numpy().flatten()
        destination_pod_embedding = self.label_embeddings.get_pod_embedding(
            trace.labels.destination_pod_label).detach().numpy().flatten()
        destination_namespace_embedding = self.label_embeddings.get_namespace_embedding(
            trace.labels.destination_namespace_label).detach().numpy().flatten()

        # Combine Source IP features with label embeddings
        source_combined_features = np.concatenate(
            [source_ip_features, source_pod_embedding, source_namespace_embedding])
        destination_combined_features = np.concatenate(
            [destination_ip_features, destination_pod_embedding, destination_namespace_embedding])

        # Ensure features sizes are adjusted to NODE_EMBEDDING_SIZE
        node_features.append(source_combined_features[:NODE_EMBEDDING_SIZE])
        node_index[trace.ip_source] = len(node_features) - 1  # Current index of source

        node_features.append(destination_combined_features[:NODE_EMBEDDING_SIZE])
        node_index[trace.ip_destination] = len(node_features) - 1  # Current index of destination

        # Add edge between source and destination
        source_idx = node_index.get(trace.ip_source)
        dest_idx = node_index.get(trace.ip_destination)
        if source_idx is not None and dest_idx is not None:
            edge_index.append([source_idx, dest_idx])
            # Add source and destination ports as edge attributes
            edge_attr.append([trace.labels.source_port_label, trace.labels.destination_port_label])

        # Convert lists to tensors
        x = torch.tensor(node_features, dtype=torch.float)
        edge_index_tensor = torch.tensor(edge_index, dtype=torch.long).t().contiguous() if edge_index else torch.empty(
            (2, 0), dtype=torch.long)
        edge_attr_tensor = torch.tensor(edge_attr, dtype=torch.float) if edge_attr else torch.empty((0, 2), dtype=torch.float)

        # Create the PyTorch Geometric Data object to encapsulate the graph data
        graph_data = Data(x=x, edge_index=edge_index_tensor, edge_attr=edge_attr_tensor)
        return graph_data
