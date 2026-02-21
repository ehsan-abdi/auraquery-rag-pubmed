import logging
import http.client
import urllib.error
from typing import List, Dict, Optional
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
        except urllib.error.HTTPError as e:
            logger.error(f"HTTPError during NCBI search (Code {e.code}): {e.reason}")
            return []
        except urllib.error.URLError as e:
            logger.error(f"URLError during NCBI search: {e.reason}")
            return []
        except http.client.IncompleteRead as e:
            logger.error(f"IncompleteRead during NCBI search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during NCBI search: {e}")
            return []

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
        except urllib.error.HTTPError as e:
            logger.error(f"HTTPError fetching records (Code {e.code}): {e.reason}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching full records: {e}")
            return []

    def fetch_pmc_links(self, pmids: List[str]) -> Dict[str, str]:
        """
        Takes a list of PMIDs, performs a single batched elink query,
        and returns a dictionary mapping PMID -> PMCID.
        """
        if not pmids:
            return {}
            
        logger.info(f"Fetching PMC links for {len(pmids)} PMIDs in batch...")
        pmid_to_pmcid = {}
        
        try:
            link_handle = Entrez.elink(dbfrom="pubmed", db="pmc", id=pmids)
            link_results = Entrez.read(link_handle)
            link_handle.close()
            
            for result in link_results:
                pmid = result.get("IdList", [])
                if not pmid:
                    continue
                pmid = pmid[0]
                
                link_sets = result.get("LinkSetDb", [])
                if not link_sets:
                    continue
                    
                links = link_sets[0].get("Link", [])
                if not links:
                    continue
                    
                pmc_id = links[0].get("Id")
                if pmc_id:
                    pmid_to_pmcid[pmid] = pmc_id
                    
            logger.info(f"Successfully mapped {len(pmid_to_pmcid)} PMIDs to PMCIDs.")
            return pmid_to_pmcid
            
        except urllib.error.HTTPError as e:
            logger.error(f"HTTPError in eLink batch (Code {e.code}): {e.reason}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching PMC links: {e}")
            return {}

    def fetch_full_text(self, pmcid: str) -> str:
        """Fetches full text XML from PMC using PMCID."""
        try:
            logger.debug(f"Fetching XML for PMCID: {pmcid}")
            fetch_handle = Entrez.efetch(
                db="pmc", id=pmcid, rettype="xml", retmode="text")
            raw_xml = fetch_handle.read()
            fetch_handle.close()

            return raw_xml
        except urllib.error.HTTPError as e:
            logger.error(f"HTTPError fetching full text for {pmcid} (Code {e.code}): {e.reason}")
            return ""
        except Exception as e:
            logger.error(f"Full text fetch failed for {pmcid}: {str(e)}")
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
