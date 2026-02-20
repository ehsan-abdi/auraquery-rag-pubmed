# AuraQuery  
### RAG-based ChatBot for PubMed Open-Access Medical Literature

AuraQuery is a modular, production-grade Retrieval-Augmented Generation (RAG) system designed to query and reason over open-access PubMed Central (PMC) medical literature.

The system implements a two-index retrieval strategy optimized for performance, relevance filtering, and scalable knowledge retrieval.

This project is built as a professional portfolio-grade AI system, emphasizing clean architecture, modular design, and production best practices.

---

## 🚀 Project Vision

AuraQuery is designed to:

- Ingest open-access biomedical literature from PubMed/PMC
- Clean and structure full-text XML into chunkable content
- Implement a dual-index retrieval strategy
- Provide high-precision document selection before LLM inference
- Serve as the backend foundation for a future Angular-based web interface

This repository focuses on backend ingestion, indexing, and retrieval architecture.

---

## 🧠 System Architecture

### Two-Index Strategy

AuraQuery uses a performance-optimized dual-index retrieval system:

### Index A — Abstract Layer
- Contains only article abstracts
- Fast filtering layer
- Used for initial semantic ranking
- Reduces search space before deep retrieval

### Index B — Body Chunk Layer
- Contains cleaned, structured body text
- Chunked for embedding
- Queried only for top-N selected papers from Index A

---

## 🔄 Retrieval Flow

```text
→ Query
→ Abstract Index
→ Select Top N Relevant Papers
→ Retrieve Body Chunks (from selected papers only)
→ Feed into LLM
→ Generate Answer
```

This architecture improves:

- Latency
- Retrieval precision
- Token efficiency
- Cost control for LLM usage

---

## 🏗 Project Structure

```text
AuraQuery/
├── app/
│   ├── core/          # Business logic (parsing, ingestion, orchestration)
│   ├── db/            # NCBI client & storage logic
│   ├── api/           # Future FastAPI endpoints
│   └── utils/         # Config, logging, helpers
├── data/
│   ├── raw/           # Ingested PubMed JSON files (ignored in Git)
│   └── processed/     # Chunked and metadata-enriched JSONs (ignored in Git)
├── scripts/           # Batch ingestion & chunking scripts
├── tests/             # Unit and integration tests
├── .env               # API keys (not committed)
├── requirements.txt
└── README.md
```

---

## 🧩 Core Components

### NCBI Client
- Uses Biopython Entrez API
- Handles search, pagination, and XML fetch
- Respects NCBI rate limits

### XML Cleaner
- Parses PMC JATS XML
- Removes references, figures, tables, formulas
- Preserves section hierarchy using Markdown-style headers

### Ingestion Pipeline
- Filters only open-access articles
- Saves structured JSON files:
  - `abstract_layer`
  - `body_layer`
- Ensures reproducible data storage

---

## ⚙️ Tech Stack

- Python
- LangChain
- Biopython (Entrez API)
- lxml (XML parsing)
- Pydantic (data models)
- Structured logging
- Modular package architecture

**Planned Extensions:**
- FastAPI (backend API layer)
- Angular (frontend interface)
- Deployment to personal website
- Docker & CI/CD pipeline

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/ehsan-abdi/auraquery-rag-pubmed.git
cd auraquery-rag-pubmed
```

#### Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

#### Install dependencies:

```bash
pip install -r requirements.txt
```

#### Create a .env file in the project root:

```bash
GOOGLE_API_KEY=
GROQ_API_KEY=
NCBI_API_KEY=
NCBI_EMAIL=
LANGCHAIN_API_KEY=
```

---

## 📥 Ingestion & Processing

#### 1. To batch ingest open-access HHT papers:

```bash
python scripts/batch_ingest_hht.py
```

Ingested JSON files will be stored in:
```bash
data/raw/hht/
```

#### 2. To process and chunk the ingested articles:

```bash
python scripts/run_chunking.py --folder hht
```

This will run the two-layer indexing strategy, chunking by markdown headers and text overlap, saving final output to:
```bash
data/processed/hht/
```

---

## 🔒 Production Considerations

- Secure API key management via .env
- Modular separation of concerns
- Centralized logging configuration
- Rate-limit aware NCBI fetching
- Scalable two-index retrieval design

---

## 🛣 Roadmap
- Vector store integration (Abstract + Body indices)
- Retrieval module implementation
- LLM answer generation chain
- FastAPI endpoints
- Angular frontend interface
- Deployment to personal website
- CI/CD pipeline
- Docker containerization

---

## 👤 Author

Ehsan Abdi
AI Engineer | Retrieval Systems | Production LLM Architectures

GitHub: https://github.com/ehsan-abdi

---

## 📄 License

This project is licensed under the MIT License.