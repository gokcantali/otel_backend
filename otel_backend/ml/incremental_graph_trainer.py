from torch_geometric.data import Data
import torch
import torch.nn.functional as F
import torch.optim as optim


class IncrementalGraphTrainer:
    async def __init__(self, model, optimizer):
        self.model = model
        self.optimizer = optimizer
        self.label_encodings = {
            'pod_label': {'encoding': {}, 'current_id': 0},
            'namespace_label': {'encoding': {}, 'current_id': 0},
            'source_port_label': {'encoding': {}, 'current_id': 0},
            'destination_port_label': {'encoding': {}, 'current_id': 0},
        }

    async def encode_label(self, label_type, label_value):
        encoding_dict = self.label_encodings[label_type]['encoding']
        current_id = self.label_encodings[label_type]['current_id']
        if label_value not in encoding_dict:
            encoding_dict[label_value] = current_id
            self.label_encodings[label_type]['current_id'] += 1
        normalized_label = encoding_dict[label_value] / max(self.label_encodings[label_type]['current_id'] - 1, 1)
        return normalized_label

    async def prepare_data(self, new_data):
        pod_label_encoded = await self.encode_label('pod_label', new_data['labels']['pod_label'])
        namespace_label_encoded = await self.encode_label('namespace_label', new_data['labels']['namespace_label'])
        source_port_label_encoded = await self.encode_label('source_port_label', new_data['labels']['source_port_label'])
        destination_port_label_encoded = await self.encode_label('destination_port_label', new_data['labels']['destination_port_label'])
        x = torch.ones((2, 1))
        edge_index = torch.tensor([[0], [1]], dtype=torch.long)
        edge_attr = torch.tensor([[pod_label_encoded, namespace_label_encoded, source_port_label_encoded, destination_port_label_encoded]], dtype=torch.float)
        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

    async def predict_anomaly_score(self, data):
        self.model.eval()
        with torch.no_grad():
            out = self.model(data)
            target = torch.tensor([[0.5, 0.5]])  # This target can be adjusted
            loss = F.mse_loss(out, target, reduction='none')
            anomaly_score = loss.mean(dim=1).item()  # Average loss as anomaly score
        return anomaly_score

    async def update_model(self, data):
        self.model.train()
        self.optimizer.zero_grad()
        out = self.model(data)
        target = torch.tensor([[0.5, 0.5]])  # Consistent target for training
        loss = F.mse_loss(out, target)
        loss.backward()
        self.optimizer.step()
        return loss.item()
