"""
Ingestion orchestrator for PubMed open-access articles.
Handles searching for papers, parsing abstracts, and concurrently fetching and cleaning full-text bodies.
"""
import json
import logging
import concurrent.futures
from typing import List, Dict, Optional

from app.utils.config import settings
from app.utils.helpers import clean_pmc_xml
from app.db.ncbi_client import ncbi_client
from app.core.parser import parse_medline
from app.models.schemas import ArticleMetadata

logger = logging.getLogger(__name__)


def _fetch_and_parse_abstracts(pmids: List[str]) -> Dict[str, ArticleMetadata]:
    """
    Fetches full NCBI records for a list of PMIDs and parses out their Metadata.

    Args:
        pmids (List[str]): List of PubMed IDs to fetch.

    Returns:
        Dict[str, ArticleMetadata]: A dictionary mapping PMIDs to their fully initialized ArticleMetadata.
    """
    raw_articles = ncbi_client.fetch_full_records(pmids)
    abstract_map: Dict[str, ArticleMetadata] = {}

    for article_xml in raw_articles:
        abstract_meta = parse_medline(article_xml, content_type="abstract")
        if not abstract_meta:
            continue

        # Extract and append the Abstract Content
        abstract_data = article_xml.get(
            "MedlineCitation", {}).get("Article", {}).get("Abstract", {})
        abstract_meta.content = "\n\n".join(
            [str(t) for t in abstract_data.get("AbstractText", [])]
        )
        abstract_map[abstract_meta.pmid] = abstract_meta

    return abstract_map


def _fetch_and_clean_body(pmcid: str) -> Optional[str]:
    """
    Worker function for threading: Fetches and cleans the full-text body for a single PMCID.

    Args:
        pmcid (str): The PubMed Central ID.

    Returns:
        Optional[str]: The cleaned markdown text of the article's body, or None if unavailable/too short.
    """
    raw_body_bytes: str = ncbi_client.fetch_full_text(pmcid)
    if not raw_body_bytes:
        return None

    body_content: str = clean_pmc_xml(raw_body_bytes)
    if len(body_content) < 500:
        return None  # Ensure the body is a substantively deep full-text

    return body_content


def _process_bodies_concurrently(pmid_to_pmcid: Dict[str, str], max_workers: int = 5) -> Dict[str, str]:
    """
    Fetches PubMed Central full-text XMLs concurrently and cleans them.

    Args:
        pmid_to_pmcid (Dict[str, str]): A mapping of PMIDs to PMCIDs.
        max_workers (int, optional): The number of concurrent worker threads. Defaults to 5.

    Returns:
        Dict[str, str]: A dictionary mapping PMIDs to their completely processed markdown body string.
    """
    body_map: Dict[str, str] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit execution tasks
        future_to_pmid = {
            executor.submit(_fetch_and_clean_body, pmcid): pmid
            for pmid, pmcid in pmid_to_pmcid.items()
        }

        # Gather results sequentially as they complete
        for future in concurrent.futures.as_completed(future_to_pmid):
            pmid = future_to_pmid[future]
            try:
                body_content = future.result()
                if body_content:
                    body_map[pmid] = body_content
                else:
                    logger.debug(f"Skipping {pmid}: Body too short or unavailable.")
            except Exception as e:
                logger.error(f"Thread error fetching body for {pmid}: {e}")

    return body_map


def _save_combined_record(abstract_meta: ArticleMetadata, body_content: str, folder_name: str = "") -> bool:
    """
    Combines abstract and body layers of an article and intelligently saves them iteratively as structured JSON to disk.

    Args:
        abstract_meta (ArticleMetadata): The initialized metadata from the abstract.
        body_content (str): The cleaned markdown full-text body string.
        folder_name (str, optional): Internal subdirectory name reflecting the data's query domain. Defaults to "".

    Returns:
        bool: True if successfully saved, False otherwise.
    """
    try:
        body_meta = abstract_meta.model_copy()
        body_meta.section = "body"
        body_meta.content = body_content

        combined_data = {
            "pmid": abstract_meta.pmid,
            "abstract_layer": abstract_meta.model_dump(),
            "body_layer": body_meta.model_dump()
        }

        file_path = settings.RAW_DATA_DIR / folder_name / f"{abstract_meta.pmid}.json"
        
        # Ensure parent director tree exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, indent=4, ensure_ascii=False)

        return True
    except Exception as e:
        logger.error(f"Failed to save {abstract_meta.pmid}: {e}")
        return False


def run_ingestion(keywords: List[str], limit: int = 10, pmids: Optional[List[str]] = None, folder_name: str = "") -> None:
    """
    Orchestrates the massive parallel ingestion of PubMed articles matching defined criteria.

    Args:
        keywords (List[str]): List of query keywords. Unused if 'pmids' is provided.
        limit (int, optional): Max results to retrieve from the NCBI term query. Defaults to 10.
        pmids (Optional[List[str]], optional): Explicit list of PMIDs to ingest, skipping term search. Defaults to None.
        folder_name (str, optional): Designation subfolder for saved disk records. Defaults to "".
    """
    if pmids is None:
        keyword_part = " OR ".join(f'"{k}"[tw]' for k in keywords)
        search_query = f'({keyword_part}) AND "free full text"[Filter]'
        pmids = ncbi_client.search_pmids(search_query, max_results=limit)

    if not pmids:
        logger.warning("No Open Access papers found.")
        return

    # 1. Parse Abstracts
    abstract_map = _fetch_and_parse_abstracts(pmids)
    if not abstract_map:
        return

    # 2. Map PMIDs to PMCIDs in one batch via ELink logic
    pmid_to_pmcid = ncbi_client.fetch_pmc_links(list(abstract_map.keys()))
    if not pmid_to_pmcid:
        logger.warning("No PMC links found for this batch.")
        return

    # 3. Fetch full bodies concurrently
    body_map = _process_bodies_concurrently(pmid_to_pmcid, max_workers=5)

    # 4. Save combined records
    saved_count = 0
    for pmid, body_content in body_map.items():
        if pmid in abstract_map:
            if _save_combined_record(abstract_map[pmid], body_content, folder_name):
                saved_count += 1
                logger.info(f"Successfully saved full-text: {pmid}")

    logger.info(f"Done. Saved {saved_count} high-quality papers.")
