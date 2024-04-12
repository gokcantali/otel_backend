import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 4 for IP + 16 for Source Pod Embedding + 16 for Source Namespace Embedding
# + 16 for Destination Pod Embedding + 16 for Destination Namespace Embedding
NODE_EMBEDDING_SIZE = 4 + 16 + 16