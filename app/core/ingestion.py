# app/core/ingestion.py
import json
import logging
from typing import List
from app.utils.config import settings
from app.utils.helpers import clean_pmc_xml
from app.db.ncbi_client import ncbi_client
from app.core.parser import parser

logger = logging.getLogger(__name__)


def run_ingestion(keywords: List[str], limit: int = 10, pmids: list = None):
    """
    Orchestrates ingestion of PubMed articles:
    - Searches NCBI using keywords
    - Parses metadata & abstract
    - Fetches full-text bodies from PMC
    - Cleans and saves JSON to RAW_DATA_DIR
    """
    if pmids is None:
        # Build query and fetch PMIDs
        keyword_part = " OR ".join(f'"{k}"[tw]' for k in keywords)
        search_query = f'({keyword_part}) AND "free full text"[Filter]'
        pmids = ncbi_client.search_pmids(search_query, max_results=limit)

    if not pmids:
        logger.warning("No Open Access papers found.")
        return

    raw_articles = ncbi_client.fetch_full_records(pmids)
    saved_count = 0

    for article_xml in raw_articles:
        # Parse abstract metadata
        abstract_meta = parser.parse_medline(
            article_xml, content_type="abstract")
        if not abstract_meta:
            continue

        # Fill abstract content
        abstract_data = article_xml.get("MedlineCitation", {}).get(
            "Article", {}).get("Abstract", {})
        abstract_meta.content = "\n\n".join(
            [str(t) for t in abstract_data.get("AbstractText", [])])

        # Fetch and clean body
        raw_body_bytes = ncbi_client.fetch_full_text(abstract_meta.pmid)
        body_content = clean_pmc_xml(raw_body_bytes)

        # Skip if body too short
        if len(body_content) < 500:
            logger.debug(
                f"Skipping {abstract_meta.pmid}: Body too short or unavailable.")
            continue

        # Prepare body metadata
        body_meta = abstract_meta.model_copy()
        body_meta.section = "body"
        body_meta.content = body_content

        # Save JSON exactly as before
        combined_data = {
            "pmid": abstract_meta.pmid,
            "abstract_layer": abstract_meta.model_dump(),
            "body_layer": body_meta.model_dump()
        }
        file_path = settings.RAW_DATA_DIR / f"{abstract_meta.pmid}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, indent=4, ensure_ascii=False)

        saved_count += 1
        logger.info(f"Successfully saved full-text: {abstract_meta.pmid}")

    logger.info(f"Done. Saved {saved_count} high-quality papers.")


# # Example usage
# if __name__ == "__main__":
#     run_ingestion(
#         ["Hereditary Hemorrhagic Telangiectasia"], limit=5
#     )
