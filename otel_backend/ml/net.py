import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv
import torch.nn as nn

class GATNet(nn.Module):
    def __init__(self, num_node_features, num_edge_features, num_classes):
        super(GATNet, self).__init__()
        self.conv1 = GATConv(num_node_features, 8, heads=8, dropout=0.6)
        self.conv2 = GATConv(8 * 8, num_classes, heads=1, concat=False, dropout=0.6)

    async def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = F.dropout(x, p=0.6, training=self.training)
        x = F.elu(self.conv1(x, edge_index))
        x = F.dropout(x, p=0.6, training=self.training)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)