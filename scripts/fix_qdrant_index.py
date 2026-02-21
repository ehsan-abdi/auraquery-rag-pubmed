import os
import sys
import logging

main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, main_dir)

from qdrant_client import QdrantClient
from qdrant_client.http.models import PayloadSchemaType
from app.utils.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fix_index")

def apply_index():
    logger.info("Connecting to Qdrant Cloud...")
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
    
    logger.info("Checking aura_index_a_abstracts indices...")
    info_a = client.get_collection("aura_index_a_abstracts")
    logger.info(f"Payload schema a: {info_a.payload_schema}")
    
    logger.info("Checking aura_index_b_bodies indices...")
    info_b = client.get_collection("aura_index_b_bodies")
    logger.info(f"Payload schema b: {info_b.payload_schema}")

    logger.info("Force applying keyword index on metadata.pmid for aura_index_b_bodies...")
    client.create_payload_index(
        collection_name="aura_index_b_bodies",
        field_name="metadata.pmid",
        field_schema=PayloadSchemaType.KEYWORD,
        wait=True
    )
    logger.info("Done! Verifying...")
    
    info_b_after = client.get_collection("aura_index_b_bodies")
    logger.info(f"Payload schema b (after): {info_b_after.payload_schema}")

if __name__ == "__main__":
    apply_index()
