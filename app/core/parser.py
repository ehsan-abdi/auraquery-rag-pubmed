"""
Parser for converting raw NCBI Medline XML into structured ArticleMetadata models.
"""
from typing import List, Optional, Dict, Any
from app.models.schemas import ArticleMetadata


def parse_medline(article_xml: Dict[str, Any], content_type: str = "abstract") -> Optional[ArticleMetadata]:
    """
    Parses a raw Medline XML dictionary into a structured ArticleMetadata model.

    Args:
        article_xml (Dict[str, Any]): The raw parsed XML data from the PubMed EFetch endpoint.
        content_type (str, optional): The section type being parsed, typically "abstract" or "body". Defaults to "abstract".

    Returns:
        Optional[ArticleMetadata]: A structured Pydantic model containing the article's metadata, 
        or None if an error occurs during parsing or required data is missing.
    """
    try:
        citation = article_xml.get("MedlineCitation", {})
        article = citation.get("Article", {})

        # Extract MeSH headings and Publication Types
        mesh_headings = citation.get("MeshHeadingList", [])
        major: List[str] = []
        minor: List[str] = []
        
        for mesh in mesh_headings:
            term = str(mesh.get("DescriptorName", ""))
            is_maj = mesh.get("DescriptorName", {}).attributes.get("MajorTopicYN") == "Y"
            if is_maj:
                major.append(term)
            else:
                minor.append(term)

        pub_types = [str(pt) for pt in article.get("PublicationTypeList", [])]

        # Determine if study refers to humans or animals from MeSH terms
        all_mesh = " ".join(major + minor).lower()

        # Extract basic citation data safely
        pmid = str(citation.get("PMID", ""))
        doi = next((str(e) for e in article.get("ELocationID", []) if e.attributes.get("EIdType") == "doi"), None)
        article_title = article.get("ArticleTitle", "")
        
        journal_info = article.get("Journal", {})
        journal_title = journal_info.get("Title", "")
        pub_year = int(journal_info.get("JournalIssue", {}).get("PubDate", {}).get("Year", 0))
        
        author_list = article.get("AuthorList", [{}])
        first_author_lastname = author_list[0].get("LastName", "Unknown") if author_list else "Unknown"
        first_author_initials = author_list[0].get("Initials", "") if author_list else ""

        return ArticleMetadata(
            pmid=pmid,
            doi=doi,
            section=content_type,
            article_title=article_title,
            journal=journal_title,
            pub_year=pub_year,
            first_author_lastname=first_author_lastname,
            first_author_initials=first_author_initials,
            mesh_major_terms=major,
            mesh_minor_terms=minor,
            publication_types=pub_types,
            is_human="humans" in all_mesh,
            is_animal="animals" in all_mesh,
            content=""  # To be filled by the orchestrator (e.g., ingestion pipeline)
        )
    except Exception:
        # If the XML format is highly anomalous, gracefully skip
        return None
