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

#### 3. To embed the processed chunks into ChromaDB:

```bash
python scripts/build_vector_store.py --folder hht
```

This will run the chunks through OpenAI's `text-embedding-3-small` model and save the resulting vectors locally to:
```bash
data/vectorstore/
```

---

## 🔍 Querying the Knowledge Base

AuraQuery comes with two built-in terminal interfaces to query your specialized vector database using the advanced hybrid retrieval pipeline:

### 1. Single-Shot Queries
Run the basic CLI tool for isolated clinical questions:
```bash
python scripts/run_query.py "What are the common genetic mutations associated with Hereditary Hemorrhagic Telangiectasia?"
```

### 2. Conversational Memory (Phase 4)
Run the interactive chat engine to engage in multi-turn dialogue with memory:
```bash
python scripts/run_chat.py
```
This engine utilizes a **Query Reformulator** to intercept conversational pronouns (e.g., "What are its side effects?"), rewrite them into standalone queries by analyzing the chat history, and seamlessly extract and carry over specific PMIDs for highly targeted follow-up retrieval.

### Phase 3 Hybrid Retrieval Architecture
Our custom engine uses **True Hybrid Search**:
1. **Abstract Layer (Index A):** A wide-net dense search over thousands of abstracts to derive candidate PMIDs.
2. **Body Chunk Layer (Index B):** A restrictive dense search drilling deeply into the isolated PMIDs.
3. **Custom Python Reranker:** We linearly boost chunks originating from **Meta-Analyses** and **RCTs**, and boost sections discussing **Results** or **Conclusions**.
4. **Diversity Guardrail:** Results are strictly capped at **3 chunks per PMID** to force multi-source synthesis and prevent single-review dominance.

---

## 🔒 Production Considerations

- Secure API key management via .env
- Modular separation of concerns
- Centralized logging configuration
- Rate-limit aware NCBI fetching
- Scalable two-index retrieval design

---

## 🛣 Roadmap
- [x] Vector store integration (Abstract + Body indices)
- [x] Retrieval module implementation
- [x] LLM answer generation chain
- [ ] FastAPI endpoints
- [ ] Angular frontend interface
- [ ] Deployment to personal website
- [ ] CI/CD pipeline
- [ ] Docker containerization

---

## 👤 Author

Ehsan Abdi
AI Engineer | Retrieval Systems | Production LLM Architectures

GitHub: https://github.com/ehsan-abdi

---

## 📄 License

This project is licensed under the MIT License.