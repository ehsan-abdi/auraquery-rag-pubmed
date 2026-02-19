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

\n→ Query
\n→ Abstract Index
\n→ Select Top N Relevant Papers
\n→ Retrieve Body Chunks (from selected papers only)
\n→ Feed into LLM
\n→ Generate Answer

This architecture improves:

- Latency
- Retrieval precision
- Token efficiency
- Cost control for LLM usage

---

## 🏗 Project Structure

AuraQuery/
\n├── app/
\n│   ├── core/          # Business logic (parsing, ingestion, orchestration)
\n│   ├── db/            # NCBI client & storage logic
\n│   ├── api/           # Future FastAPI endpoints
\n│   └── utils/         # Config, logging, helpers
\n├── data/
\n│   └── raw/           # Ingested PubMed JSON files (ignored in Git)
\n├── scripts/           # Batch ingestion scripts
\n├── tests/             # Unit and integration tests
\n├── .env               # API keys (not committed)
\n├── requirements.txt
\n└── README.md

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

## 📥 Ingesting Open-Access Literature

#### To batch ingest open-access HHT papers:

```bash
python scripts/batch_ingest_hht.py
```

#### Ingested JSON files will be stored in:

```bash
data/raw/
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