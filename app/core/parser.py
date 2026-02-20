from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ArticleMetadata(BaseModel):
    pmid: str
    doi: Optional[str] = None
    section: str  # "abstract" or "body"
    article_title: str
    journal: str
    pub_year: int
    first_author_lastname: str = "Unknown"
    first_author_initials: str = ""
    mesh_major_terms: List[str] = Field(default_factory=list)
    mesh_minor_terms: List[str] = Field(default_factory=list)
    publication_types: List[str] = Field(default_factory=list)
    is_human: bool = False
    is_animal: bool = False
    content: str  # The actual text (Abstract or Body)


def parse_medline(article_xml: Dict, content_type: str = "abstract") -> Optional[ArticleMetadata]:
        try:
            citation = article_xml.get("MedlineCitation", {})
            article = citation.get("Article", {})

            # MeSH & PubTypes
            mesh_headings = citation.get("MeshHeadingList", [])
            major, minor = [], []
            for mesh in mesh_headings:
                term = str(mesh.get("DescriptorName", ""))
                is_maj = mesh.get("DescriptorName", {}).attributes.get(
                    "MajorTopicYN") == "Y"
                major.append(term) if is_maj else minor.append(term)

            pub_types = [str(pt)
                         for pt in article.get("PublicationTypeList", [])]

            # Logic for human/animal
            all_mesh = " ".join(major + minor).lower()

            return ArticleMetadata(
                pmid=str(citation.get("PMID", "")),
                doi=next((str(e) for e in article.get("ELocationID", [])
                         if e.attributes.get("EIdType") == "doi"), None),
                section=content_type,
                article_title=article.get("ArticleTitle", ""),
                journal=article.get("Journal", {}).get("Title", ""),
                pub_year=int(article.get("Journal", {}).get(
                    "JournalIssue", {}).get("PubDate", {}).get("Year", 0)),
                first_author_lastname=article.get("AuthorList", [{}])[
                    0].get("LastName", "Unknown"),
                first_author_initials=article.get("AuthorList", [{}])[
                    0].get("Initials", ""),
                mesh_major_terms=major,
                mesh_minor_terms=minor,
                publication_types=pub_types,
                is_human="humans" in all_mesh,
                is_animal="animals" in all_mesh,
                content=""  # Filled by the Orchestrator
            )
        except Exception:
            return None


# end of file
