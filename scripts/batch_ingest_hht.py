import time
import logging
from app.db.ncbi_client import ncbi_client
from app.core.ingestion import run_ingestion
from app.utils.logging import setup_logging

setup_logging(level="INFO")
logger = logging.getLogger(__name__)

# ------------- CONFIG -------------
KEYWORDS = ["Osler-Weber-Rendu", "Osler Weber Rendu", "Hereditary Hemorrhagic Telangiectasia"]
BATCH_SIZE = 50
DELAY_BETWEEN_BATCHES = 0.3  # seconds
# ----------------------------------


def run_ingestion_for_pmids(pmids):
    """
    Ingest only a list of PMIDs, reusing core.ingestion logic.
    """
    run_ingestion(keywords=[], limit=0, pmids=pmids, folder_name="hht")


def main():
    query = " OR ".join(f'"{k}"[tw]' for k in KEYWORDS)
    query += ' AND "free full text"[Filter]'

    total_hits = ncbi_client.get_total_hits(query)
    logger.info(f"Total Open Access HHT papers found: {total_hits}")

    retstart = 0
    while retstart < total_hits:
        pmids = ncbi_client.search_pmids(
            query, max_results=BATCH_SIZE, retstart=retstart)
        if not pmids:
            logger.warning("No more PMIDs returned, stopping.")
            break

        logger.info(f"Processing batch: {retstart} → {retstart + len(pmids)}")
        run_ingestion_for_pmids(pmids)
        retstart += BATCH_SIZE
        time.sleep(DELAY_BETWEEN_BATCHES)

    logger.info("All batches completed.")


if __name__ == "__main__":
    main()
