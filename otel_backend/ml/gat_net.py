from hashlib import sha256

import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GATConv

from otel_backend.ml import NODE_EMBEDDING_SIZE
from otel_backend.ml.extract import Trace


class LabelEmbeddings:
    def __init__(self, embedding_dim=16):
        self.pod_embeddings = torch.nn.Embedding(num_embeddings=1000, embedding_dim=embedding_dim)
        self.namespace_embeddings = torch.nn.Embedding(num_embeddings=1000, embedding_dim=embedding_dim)
        self.port_embeddings = torch.nn.Embedding(num_embeddings=65536, embedding_dim=embedding_dim)  # For ports, assuming a max of 65535
        self.label_to_index = {}
        self.label_counter = 0

    def get_embedding(self, label):
        if label not in self.label_to_index:
            self.label_to_index[label] = self.label_counter
            self.label_counter += 1
        return self.port_embeddings(torch.tensor([self.label_to_index[label]], dtype=torch.long))

def hash_ip(ip_address, feature_length=16):
    hash_digest = sha256(ip_address.encode()).digest()
    return np.array([b for b in hash_digest[:feature_length]], dtype=np.float32) / 255

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
        edge_attr = []
        node_index = {}

        # Extract IP address features
        source_ip_features = hash_ip(trace.ip_source)
        destination_ip_features = hash_ip(trace.ip_destination)

        # Get embeddings for pod and namespace labels
        source_pod_embedding = self.label_embeddings.get_embedding(
            trace.labels.source_pod_label).detach().numpy().flatten()
        source_namespace_embedding = self.label_embeddings.get_embedding(
            trace.labels.source_namespace_label).detach().numpy().flatten()
        destination_pod_embedding = self.label_embeddings.get_embedding(
            trace.labels.destination_pod_label).detach().numpy().flatten()
        destination_namespace_embedding = self.label_embeddings.get_embedding(
            trace.labels.destination_namespace_label).detach().numpy().flatten()

        # Embed port data
        source_port_embedding = self.label_embeddings.get_embedding(
            trace.labels.source_port_label).detach().numpy().flatten()
        destination_port_embedding = self.label_embeddings.get_embedding(
            trace.labels.destination_port_label).detach().numpy().flatten()

        # Combine Source IP features with label embeddings
        source_combined_features = np.concatenate(
            [source_ip_features, source_pod_embedding, source_namespace_embedding])
        destination_combined_features = np.concatenate(
            [destination_ip_features, destination_pod_embedding, destination_namespace_embedding])

        node_features.append(source_combined_features[:NODE_EMBEDDING_SIZE])
        node_index[trace.ip_source] = len(node_features) - 1

        node_features.append(destination_combined_features[:NODE_EMBEDDING_SIZE])
        node_index[trace.ip_destination] = len(node_features) - 1

        source_idx = node_index.get(trace.ip_source)
        dest_idx = node_index.get(trace.ip_destination)
        if source_idx is not None and dest_idx is not None:
            edge_index.append([source_idx, dest_idx])
            # Convert TCP flags to integer and include them in edge attributes
            ack_flag = int(trace.labels.ack_flag)
            psh_flag = int(trace.labels.psh_flag)
            edge_attr.append(np.concatenate([source_port_embedding, destination_port_embedding, [ack_flag, psh_flag]]))

        x = torch.tensor(node_features, dtype=torch.float)
        edge_index_tensor = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_attr_tensor = torch.tensor(edge_attr, dtype=torch.float) if edge_attr else torch.empty(
            (0, 2 * self.label_embeddings.embedding_dim + 2), dtype=torch.float)

        return Data(x=x, edge_index=edge_index_tensor, edge_attr=edge_attr_tensor)

