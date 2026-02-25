# 🧠 AuraQuery: Biomedical RAG Engine

AuraQuery is an advanced, production-grade Conversational Retrieval-Augmented Generation (RAG) system engineered specifically for searching, analyzing, and synthesizing open-access biomedical literature from PubMed. 

Instead of relying on general-purpose search, AuraQuery implements a **Four-Stage Hybrid Retrieval Pipeline** backed by sophisticated LLM query optimization and custom citation generation, guaranteeing highly accurate, evidence-based answers with zero hallucination.

---

## 🏗️ End-to-End Architecture

AuraQuery's architecture is decoupled into five distinct operational stages:

### 1. Data Ingestion & Preprocessing
The ingestion pipeline automates the downloading and initial structuring of academic papers.
*   **NCBI Entrez Integration (`ncbi_client.py`)**: Fetches PubMed IDs, resolves PubMed Central (PMC) links, and downloads full-text XMLs.
*   **Medline Parsing (`parser.py`)**: Converts raw XML into structured Pydantic schemas (`ArticleMetadata`), explicitly extracting clinical MeSH terms, publication types, doic/pmid, and author information.
*   **Cleaning & Combining**: Layers the article abstract and full-text body into a single JSON record.

### 2. Multi-Index Text Chunking
To balance broad context discovery with deep semantic precision, `AuraChunker` produces two indices:
*   **Index A (Abstracts)**: Preserves the entire abstract as a single document for wide, conceptual matching.
*   **Index B (Full Text Body)**: Semantically splits the body by Markdown headers (e.g., Results, Methods), then falls back to recursive character chunking to ensure LLM context limits are respected.

### 3. Hybrid Vectorization & Storage
AuraQuery relies on **Qdrant Cloud** for high-performance Vector Search, wrapped cleanly in `AuraVectorStore`.
*   **Dense Embeddings**: Maps semantic meaning using OpenAI's `text-embedding-3-small`.
*   **Sparse Embeddings (BM25)**: Ensures exact keyword matches (crucial for complex medical/gene terminology) via `FastEmbedSparse`.

### 4. Advanced 4-Stage Query Processing & Retrieval
The retrieval process is hyper-tuned for clinical accuracy and diversity. It is managed by `QueryParser` and `AuraRetriever`:
1.  **LLM Query Parsing**: The user's query is analyzed by `gpt-4o-mini`. Ambiguous terms are flagged for user clarification. Otherwise, the query is expanded for Hybrid Search, and strict metadata filters (Authors, Year) are decoupled.
2.  **Stage 1 - Abstract Discovery**: Searches Index A to find the most conceptually relevant papers (Candidate PMIDs).
3.  **Stage 2 - Deep Chunk Search**: Drills exclusively into Index B of the Candidate PMIDs to find the specific paragraphs containing the answer.
4.  **Stage 3 - Algorithmic Reranking**: Boosts chunks based on **Methodology** (e.g., RCTs > Case Reports), **Section** (e.g., Results > Introduction), and **Recency**.
5.  **Stage 4 - Diversity Filtering**: Caps the number of chunks pulled from any single paper so a single comprehensive review article doesn't drown out novel primary research.

### 5. Chat Engine & Response Generation
*   **`AuraChatEngine`**: Maintains isolated conversational memories. It intercepts conversational follow-ups and explicitly resolves pronouns and historical PMIDs into standalone search queries.
*   **`AuraQAChain`**: Assembles the curated chunks into a strictly formatted prompt. Forces the LLM to output professional clinical answers and enforces **in-line Harvard-style citations** mapped directly to the original PMIDs. If no evidence is found, it triggers a global fallback search on Index B before admitting defeat.

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   OpenAI API Key
*   NCBI Entrez API Key & Email
*   Qdrant Cloud URL & API Key

Set these in a `.env` file at the root of the project.

### Running the API
AuraQuery serves a FastAPI backend for frontend integration (e.g., Angular dashboards).
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Running the CLI Engine
You can interface directly with the conversation engine via the terminal:

**Interactive Chat Session:**
```bash
python scripts/run_chat.py
```

**Single Query Shot:**
```bash
python scripts/run_query.py "What are the common symptoms of Hereditary Hemorrhagic Telangiectasia?"
```

### Updating the Database (Ingestion)
To ingest new batches of literature into your Qdrant cluster:
```bash
python scripts/batch_ingest_hht.py
```

---

## 📂 Project Layout

```text
AuraQuery/
├── app/
│   ├── main.py                # FastAPI Application Entry
│   ├── api/                   # REST API Endpoints
│   ├── core/                  # Core RAG Logic (Retrieval, Parsing, Chat)
│   ├── db/                    # Vector Store and NCBI wrappers
│   ├── models/                # Pydantic Schemas
│   └── utils/                 # Config & Helpers
├── scripts/                   # CLI Tools for Search & Ingestion
├── tests/                     # Automated testing suite
├── Dockerfile
└── requirements.txt
```

---

*For issues, enhancements, or clinical integrations, please review the issue tracker.*