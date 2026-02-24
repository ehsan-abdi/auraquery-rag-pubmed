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
QDRANT_URL=
QDRANT_API_KEY=
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

#### 3. To migrate the chunks to Qdrant Cloud (Dense + Sparse Vectors):

```bash
python scripts/migrate_to_qdrant.py
```

This script generates **BM25 Sparse Vectors** (via `FastEmbed`) and OpenAI Dense Vectors on the fly, pushing them to a native Hybrid Qdrant Cloud cluster.

---

## 🔍 Specialized Hybrid Retrieval

AuraQuery executes a highly optimized **Reciprocal Rank Fusion (RRF)** retrieval pipeline:

1. **Abstract Layer (Index A):** A wide-net semantic search over abstracts to derive candidate PMIDs.
2. **Body Layer (Index B):** Qdrant performs a native **Dense + Sparse Hybrid Search** strictly filtered to the Candidate PMIDs.
   - *Dense Vector:* Captures the semantic "meaning" (e.g., tying "blood thinners" to "anticoagulants").
   - *Sparse Vector:* Laser-targets exact clinical jargon (e.g., specific mutations like "c.1466del").
3. **Custom Python Reranker:** We algorithmically boost chunks originating from **RCTs, Meta-Analyses**, and **Recent Publications**. 
4. **Diversity Guardrail:** Results are hard-capped at **5 chunks per PMID** to force multi-source synthesis.

### Conversational Memory (Phase 4)
Run the interactive terminal chat engine to engage in multi-turn dialogue:
```bash
python scripts/run_chat.py
```
This engine utilizes a **Query Reformulator** to intercept conversational pronouns (e.g., "What are its side effects?"), rewrite them into standalone queries, and extract explicit metadata filters (like PMIDs) from the chat history.

---

## ☁️ FastAPI Backend (Phase 6)

AuraQuery has transitioned to a production-ready Web API connecting to the remote Qdrant Cloud cluster.

To run the scalable REST backend locally:
```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```
You can interact with the RAG pipeline graphically via the Swagger UI at `http://localhost:8000/docs`.

**Core Endpoints:**
- `POST /api/chat`: Submit queries with a `session_id` to leverage memory-aware conversational retrieval.
- `GET /api/health`: Check database integration status.

---

## 📊 LLM-as-a-Judge Evaluation Framework

AuraQuery includes a robust, autonomous RAG evaluation pipeline to quantitatively benchmark retrieval and generation performance.

#### Generating the Static Test Bank
We dynamically fetch random raw articles and prompt a Teacher LLM to generate 99 highly-specific, stateless clinical questions (along with their Ground Truth answers).
```bash
python scripts/run_evaluation.py generate 33
```

#### Evaluating the Chatbot
We pass the 99 questions to the Aura Chatbot, and use a Judge LLM (`gpt-4o-mini`) to grade the generated responses (0-10) against the hidden Ground Truth. The Judge explicitly penalizes hallucination and failure to cite reliable PMIDs.
```bash
python scripts/run_evaluation.py evaluate 60
```
This loop generates a comprehensive `data/evaluation_results.csv` tracking latency, accuracy, and detailed grading reasoning for every automated test.

---

## 🔒 Production Considerations

- Secure API key management via `.env`
- Static Test Caching to minimize LLM evaluation costs
- Rate-limit aware NCBI and OpenAI execution
- Zero local-state vector dependency (Qdrant Cloud)

---

## 🛣 Roadmap
- [x] Abstract + Body indices implementation
- [x] Two-stage Retrieval & Refined Generation
- [x] True Hybrid Search Migrated to Qdrant Cloud
- [x] Automated LLM-as-a-Judge Evaluation Pipeline
- [x] FastAPI REST endpoints
- [x] Angular Frontend Chat Interface
- [ ] Cloud Deployment (GCP / AWS / Firebase)
- [ ] Docker containerization

---

## 👤 Author

Ehsan Abdi
AI Engineer | Retrieval Systems | Production LLM Architectures

GitHub: https://github.com/ehsan-abdi

---

## 📄 License

This project is licensed under the MIT License.