import logging
from typing import List, Dict
from Bio import Entrez
from app.utils.config import settings

# Setup logging for production-grade visibility
logger = logging.getLogger(__name__)


class NCBIClient:
    def __init__(self):
        """Initialize Entrez with credentials from settings."""
        Entrez.email = settings.NCBI_EMAIL
        Entrez.api_key = settings.NCBI_API_KEY
        self.tool = "AuraQuery"

    def search_pmids(self, query: str, max_results: int = 10, retstart: int = 0) -> List[str]:
        """
        Search PubMed for keywords ORed together.
        Supports pagination via retstart.
        Returns a list of PMIDs.
        """
        logger.info(
            f"Searching PubMed with query: {query} (start={retstart}, max={max_results})")
        try:
            handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=max_results,
                retstart=retstart
            )
            record = Entrez.read(handle)
            handle.close()

            pmids = record.get("IdList", [])
            logger.info(f"Found {len(pmids)} PMIDs in this batch.")
            return pmids
        except Exception as e:
            logger.error(f"Error during NCBI search: {e}")
            return []

    # def search_pmids(self, query: str, max_results: int = 10) -> List[str]:
    #     """
    #     Search PubMed for keywords ORed together.
    #     Returns a list of PubMed IDs (PMIDs).
    #     """
    #     logger.info(f"Searching PubMed with query: {query}")

    #     try:
    #         handle = Entrez.esearch(
    #             db="pubmed", term=query, retmax=max_results)
    #         record = Entrez.read(handle)
    #         handle.close()

    #         pmids = record.get("IdList", [])
    #         logger.info(f"Found {len(pmids)} PMIDs.")
    #         return pmids
    #     except Exception as e:
    #         logger.error(f"Error during NCBI search: {e}")
    #         return []

    def fetch_full_records(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch full XML records for a list of PMIDs.
        This provides the abstract, metadata, and (where available) PMC links.
        """
        if not pmids:
            return []

        pmid_string = ",".join(pmids)
        logger.info(f"Fetching full records for PMIDs: {pmid_string}")

        try:
            # We use efetch to get the full XML data
            handle = Entrez.efetch(
                db="pubmed",
                id=pmid_string,
                retmode="xml",
                rettype="abstract"
            )
            records = Entrez.read(handle)
            handle.close()

            # Entrez.read returns a MedlineCitation or PubmedArticle list
            return records.get("PubmedArticle", [])
        except Exception as e:
            logger.error(f"Error fetching full records: {e}")
            return []

    def fetch_full_text(self, pmid: str) -> str:
        """Fetches full text from PMC."""
        try:
            # 1. Convert PMID to PMCID
            # We specifically look for the 'pubmed_pmc' link
            link_handle = Entrez.elink(dbfrom="pubmed", db="pmc", id=pmid)
            link_results = Entrez.read(link_handle)
            link_handle.close()

            # Check if any links to PMC exist
            if not link_results[0]["LinkSetDb"]:
                logger.warning(
                    f"No PMC link found for PMID: {pmid} (Paper might be behind a paywall)")
                return ""

            # Extract the actual PMCID
            links = link_results[0]["LinkSetDb"][0]["Link"]
            pmcid = links[0]["Id"]

            logger.info(
                f"Found PMCID: {pmcid} for PMID: {pmid}. Fetching XML...")

            # 2. Fetch full text XML using the PMCID
            fetch_handle = Entrez.efetch(
                db="pmc", id=pmcid, rettype="xml", retmode="text")
            raw_xml = fetch_handle.read()
            fetch_handle.close()

            return raw_xml
        except Exception as e:
            logger.error(f"Full text fetch failed for {pmid}: {str(e)}")
            return ""

    def get_total_hits(self, query: str) -> int:
        """
        Return total number of PubMed hits for a query.
        """
        try:
            handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=0  # Only need the count
            )
            record = Entrez.read(handle)
            handle.close()
            return int(record.get("Count", 0))
        except Exception as e:
            logger.error(f"Error fetching total hits: {e}")
            return 0


# Singleton for easy access
ncbi_client = NCBIClient()
