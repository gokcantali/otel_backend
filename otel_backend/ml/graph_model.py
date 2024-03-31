import torch.optim as optim

from otel_backend.ml import logger
from otel_backend.ml.extract import extract_data
from otel_backend.ml.incremental_graph_trainer import IncrementalGraphTrainer
from otel_backend.ml.net import Net


GRAPH_MODEL = None


class GraphModel:
    async def __init__(self):
        self.model = Net(num_node_features=1, num_edge_features=4, num_classes=2)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.01)
        self.trainer = IncrementalGraphTrainer(self.model, self.optimizer)

    async def train(self, new_data):
        extracted_data = await extract_data(new_data)
        data = await self.trainer.prepare_data(extracted_data)
        anomaly_score = await self.trainer.predict_anomaly_score(data)
        loss = await self.trainer.update_model(data)
        logger.info(f"Anomaly Score: {anomaly_score}, Loss: {loss}")
        return anomaly_score, loss


async def get_graph_model():
    global GRAPH_MODEL
    if GRAPH_MODEL is None:
        GRAPH_MODEL = GraphModel()
    return GRAPH_MODEL
