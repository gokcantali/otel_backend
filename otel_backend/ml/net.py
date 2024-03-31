from torch.nn import Sequential, Linear, ReLU
from torch_geometric.nn import NNConv, global_mean_pool
import torch
import torch.nn.functional as F
import torch.optim as optim


class Net(torch.nn.Module):
    async def __init__(self, num_node_features, num_edge_features, num_classes):
        super(Net, self).__init__()
        nn = Sequential(Linear(num_edge_features, 8), ReLU(), Linear(8, num_node_features * num_classes))
        self.conv = NNConv(num_node_features, num_classes, nn, aggr='mean')
        self.fc = Linear(num_classes, num_classes)

    async def forward(self, data):
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        x = F.relu(self.conv(x, edge_index, edge_attr))
        x = global_mean_pool(x, torch.zeros(data.num_nodes, dtype=torch.long))
        x = self.fc(x)
        return x
