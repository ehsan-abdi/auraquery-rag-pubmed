---
marp: true
theme: default
paginate: true
header: "**AuraQuery**: Building a Biomedical Multi-Agent RAG"
footer: "Educational Architecture Review"
style: |
  section { font-size: 24px; }
  h1 { color: #2c3e50; font-size: 40px; margin-bottom: 20px;}
  h2 { color: #34495e; font-size: 32px; margin-bottom: 15px;}
  h3 { color: #2980b9; font-size: 24px; }
  table { width: 100%; border-collapse: collapse; margin-top: 10px; }
  th { background-color: #ecf0f1; padding: 10px; text-align: left; }
  td { padding: 10px; border-bottom: 1px solid #bdc3c7; }
  .mermaid { background: white; padding: 10px; border-radius: 8px; text-align: center; }
---

# 📖 The AuraQuery Journey
## From Raw Medical Papers to an Intelligent RAG Chatbot

**Welcome!** 
Today, we are walking through the end-to-end journey of building AuraQuery: a specialized, production-grade Retrieval-Augmented Generation (RAG) system.

**Our Objective:**
To build a system capable of answering profound biomedical questions by exclusively reading the **PubMed Open Access** literature.

*Let's dive into the architectural decisions, trade-offs, and lessons learned along the way.*

---

# 1️⃣ The Challenge: PubMed & Biomedical RAG

### Why PubMed?
We started with the PubMed Open Access database because it represents the gold standard of verified, peer-reviewed biomedical knowledge. 

### Inherent Challenges:
- **Lexical Complexity:** LLMs confuse genes (e.g., *APC*) with common nouns.
- **Review Dominance:** Generic searches return highly-cited, generic review articles rather than cutting-edge, specific Randomized Controlled Trials (RCTs).
- **Format Chaos:** Downloading an XML paper gives us thousands of lines of unreadable markup, references, and formulas.

*We needed a structured way to clean and ingest this chaos.*

---

# 2️⃣ Data Ingestion & Preprocessing

**Decision:** We adopted a **Two-Tier JSON Strategy** instead of dumping full articles into one massive bucket.

| Tier 1: Abstract + Metadata | Tier 2: Full-Text + Metadata |
| :--- | :--- |
| **Purpose:** Fast, broad semantic filtering. | **Purpose:** Deep dive into the actual science. |
| **Size:** 1 JSON file per article abstract. | **Size:** 1 JSON file containing all body sections. |
| **Why?** It prevents the database from drowning in background noise when searching across thousands of papers. | **Why?** Allows the LLM to read the exact Methods or Results of a paper once we know the paper is relevant. |

**Cleaning Strategy:** We stripped out noisy XML tags and used recursive markdown indicators (`##`) to strictly preserve section headers (e.g., *## Introduction*, *## Results*). This is crucial for later reranking!

---

# 3️⃣ Semantic Chunking Strategy

To fit large papers into the LLM context limits, we had to "chunk" the data.

### Our Strategy: Section-Based (Semantic) Chunking
We didn't just chop text every 500 words. We chunked *semantically* by the `##` section headers. 
- **Abstracts:** Kept as a single chunk.
- **Body Text:** Split by section. If a section was still too large, we applied a **Max-Token + 20% Overlap** sliding window.

*Average Result:* ~10-15 highly contextualized body chunks per article.

![Semantic Chunking Diagram](https://mermaid.ink/svg/Z3JhcGggTFIKICAgIEFbUmF3IFhNTCBEb2N1bWVudF0gLS0+IEIoQWJzdHJhY3QgQ2h1bmspCiAgICBBIC0tPiBDKEJvZHkgQ2h1bmtzKQogICAgQyAtLT4gRFsjIyBJbnRyb2R1Y3Rpb25dCiAgICBDIC0tPiBFWyMjIE1ldGhvZHNdCiAgICBDIC0tPiBGWyMjIFJlc3VsdHNd)

---

# 4️⃣ Embedding the Knowledge

Once chunked, text must be translated into numbers (Vectors) so the database can understand meaning rather than just exact spellings.

### The Decision: OpenAI `text-embedding-3-small` vs. ColBERT

| Feature | OpenAI `text-embedding-3` (Dense) | ColBERT (Late Interaction / Sparse) |
| :--- | :--- | :--- |
| **Cost** | Extremely cheap (&lt;$0.0001 / 1k tokens) | Very computationally expensive |
| **Speed** | Lightning fast | Slower at scale |
| **Accuracy** | Good semantic understanding | Unbeatable clinical exact-match accuracy |
| **Storage** | Small footprint (~1536 dims) | Massive storage required |

**Verdict:** For this experimental stage, we chose OpenAI for speed and cost-efficiency. *(ColBERT remains a powerful upgrade path for the future).*

---

# 5️⃣ The Vector Database (Local ChromaDB)

We needed a place to store our millions of embeddings.

**Our Choice:** Local ChromaDB
**Pros:** Free, runs entirely on our laptop, instant setup, no cloud credentials required for experimentation.

**Cons / The Missing Feature Challenge:**
Out of the box, ChromaDB **does not support native Hybrid Search** (combining Dense Vectors with BM25 Keyword Search). In biomedical research, exact keyword matches (e.g., *ACVRL1*) are just as important as semantic meaning.

*This limitation forced us to build a custom, multi-stage retrieval pipeline using LangChain.*

---

# 6️⃣ The AuraQuery Retrieval Pipeline 

Because we lacked native Hybrid Search, we designed a **Multi-Stage Filtering & Reranking Architecture.**

![Hybrid Search Architecture](https://mermaid.ink/svg/Zmxvd2NoYXJ0IFRECiAgICBRW1VzZXIgUXVlcnldIC0tPiBBKFN0YWdlIDE6IEluZGV4IEEgLSBBYnN0cmFjdCBTZWFyY2gpCiAgICBBIC0tPnxFeHRyYWN0cyBUb3AgUE1JRHN8IEIoU3RhZ2UgMjogSW5kZXggQiAtIEJvZHkgQ2h1bmsgU2VhcmNoKQogICAgQiAtLT4gQ3tTdGFnZSAzOiBSZXJhbmtpbmcgRW5naW5lfQogICAgQyAtLT4gRFtTdGFnZSA0OiBEaXZlcnNpdHkgRmlsdGVyXQogICAgRCAtLT4gRSgoRmluYWwgQ2h1bmtzIGZvciBMTE0pKQ==)

**Why this matters:** Stage 1 casts a wide net to find the right *papers*. Stage 2 drills deeply into *only* those papers to find the right *paragraphs*.

---

# 6b️⃣ Justifying the Custom Reranker & Diversity

Instead of trusting the raw vector similarity scores, we applied our own biomedical rules:

1. **Publication Type Weighting:** +1.0 for Meta-Analyses and RCTs, +0.3 for Case Reports. This guarantees the highest quality evidence floats to the top.
2. **Recency Decay:** Applying a math decay function so a 2024 paper scores higher than a 1999 paper, all else being equal.
3. **Section Boosting:** Chunks from `## Results` or `## Conclusions` get a massive boost over `## Introduction`.
4. **Diversity Enforcer:** We hard-capped results at **Max 3 chunks per PMID**. This forces the LLM to synthesize an answer from *multiple* authors.

---

# 7️⃣ Conversational Memory (The Architect's Secret)

*The biggest trap in RAG is conversational pronouns. If a user asks a follow-up: "What are its side effects?", the Vector DB will search for "its" and fail.*

### The Two-Level Prompt Engineering Strategy

1. **The Interceptor (Chat History):** An LLM reads the chat history, resolves pronouns, and extracts explicit PMIDs. 
   - *"What are its side effects?"* ➔ *"What are the side effects of Bevacizumab PMID 123456?"*
2. **The Parser:** Another LLM optimizes the query syntax and explicitly extracts metadata (e.g., `publication_year: 2024`, `first_author: Shovlin`) to inject directly into ChromaDB filters.

*We implemented this logic using LangChain's PromptTemplates, isolating conversation logic away from mathematical retrieval logic.*

---

# 8️⃣ Answer Generation (The Synthesizer)

The final stage is generating the answer for the user based *only* on the retrieved chunks.

### LLM Choice: `gpt-4o-mini`
- It is exceptionally fast and cost-effective, yet punches far above its weight for reasoning and formatting.

### Critical Parameter Setting: `Temperature = 0.0`
- Temperature controls "creativity". In medical literature, creativity is dangerous. By freezing it to `0.0`, we force the LLM to be highly deterministic and glued entirely to the exact source text retrieved.
- **Top-p:** Left at default (1.0) since a frozen temperature naturally forces it to pick the highest probability token anyway.

---

# ☁️ Looking Ahead: Strategic Next Steps 

The Local Backend architecture is complete. Here is what is coming next:

## 9️⃣ Phase 5: Cloud Database Migration
- Transitioning from local ChromaDB to a Managed Cloud Vector DB (e.g., Pinecone or Qdrant) for scalable, always-on access.

## 🔟 Phase 6: Web Application Development
- Wrapping the Python engine in FastAPI.
- Building a sleek Angular Front-End focusing on UX.

---

# 📈 Phase 7: Analytics & Improvements

## 1️⃣1️⃣ Performance Metrics
- Implementing frameworks (like RAGAS) to quantitatively measure retrieval precision, context recall, and hallucination rates.

## 1️⃣2️⃣ Future Enhancements
- Upgrading to ColBERT late-interaction embeddings for exact-match clinical precision.
- Incorporating Journal Impact Factor into the custom reranking algorithm.

---

# 💬 Thank You! Let's Discuss

### Any questions on:
- The Multi-Agent Interceptor pattern?
- Why we prioritized RCTs via Python Reranking instead of Vector Distance?
- The Two-Tier JSON dataset design?

---
*Note: To view the flowcharts properly, open this markdown file in a viewer that supports Mermaid.js, or copy the `mermaid` code blocks into https://mermaid.live*
