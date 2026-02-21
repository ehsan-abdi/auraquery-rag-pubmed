import os
import sys

main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, main_dir)

from qdrant_client import QdrantClient
from app.utils.config import settings

client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY
)

points, _ = client.scroll(
    collection_name="aura_index_a_abstracts",
    limit=1,
    with_payload=True,
    with_vectors=False
)
print(points[0].payload)
