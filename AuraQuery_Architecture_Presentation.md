---
marp: true
theme: default
paginate: true
header: "**AuraQuery**: Biomedical Multi-Agent RAG Architecture"
footer: "Confidential - Internal Architecture Review"
style: |
  section {
    font-size: 28px;
  }
  h1 {
    color: #2c3e50;
  }
  h2 {
    color: #34495e;
  }
---

# 🧠 AuraQuery Architecture Review
## Production-Grade Biomedical RAG Chatbot

**Objective:**
Build an intelligent, highly accurate conversational agent that reasons strictly over verified, open-access medical literature.

**Key Challenges Overcome:**
- LLM Hallucinations in medical data
- Naive vector search failing on complex clinical terminology
- Conversational pronouns breaking semantic retrieval
- Review articles drowning out high-quality primary research (RCTs)

---

# 🏗️ High-Level System Architecture

AuraQuery operates as a **Multi-Agent** pipeline where distinct AI components handle specific tasks in a chain.

1. **The Interceptor Agent:** Contextualizes conversational memory.
2. **The Parser Agent:** Extracts metadata and optimizes biological query syntax.
3. **The Hybrid Retrieval Engine:** Dual-index vector search & reranking.
4. **The Synthesizer Agent:** Generates the final, perfectly cited medical response.

*Let's break down each step.*

---

# 1️⃣ The Interceptor Agent (Conversational Memory)

*Problem:* "What are its side effects?" breaks vector databases because "its" is mathematically invisible.

**Our Solution: Query Reformulation**
- Before reaching the database, an LLM evaluates the user's input against the rolling Chat History.
- **Action:** Resolves pronouns into explicit nouns.
- **Action:** Extracts specific `PMIDs` if the user refers to "these papers".
- **Result:** The system never searches for conversational noise.

*Example:* `What are its side effects?` ➔ `What are the side effects of Bevacizumab in HHT patients?`

---

# 2️⃣ The Parser Agent (Intent Optimization)

Once the query is cleanly standalone, the **QueryParser** intercepts it.

- It extracts explicit **Metadata** into a strict JSON schema:
  - `publication_year`
  - `first_author_lastname`
- It optimizes the biological phrasing (e.g., expanding abbreviations like HHT to Hereditary Hemorrhagic Telangiectasia) to maximize BM25 / Vector matching.
- **Safeguard:** It detects critically ambiguous acronyms and pauses the pipeline to ask the user for clarification before retrieving bad data.

---

# 3️⃣ The Hybrid Retrieval Engine

We completely abandoned standard single-pass vector search for a custom **Two-Stage Pipeline** with **Algorithm Reranking**.

**Stage 1: The Wide Net (Index A)**
- Searches purely over Article Abstracts to find a pool of Candidate PMIDs.

**Stage 2: The Deep Dive (Index B)**
- Strictly filters the body-text database to search *only* within the PMIDs identified in Stage 1.

---

# ⚙️ Custom Reranking & Diversity

We built a custom algorithmic reranker to ensure clinical excellence:

*   **Publication Type Weighting:** Automatically boosts Randomized Controlled Trials (RCTs) and Meta-Analyses over basic Case Reports.
*   **Recency Decay:** Mathematically applies a gentle exponential decay based on `publication_year` to favor modern findings.
*   **Section Weighting:** Boosts chunks originating from the *Results* or *Conclusions* sections of the XML.
*   **Diversity Constraint:** Hard-capped at 3 chunks per PMID to mathematically force the LLM to read multiple papers instead of lazily summarizing one long review article.

---

# 4️⃣ The Synthesizer Agent (Generation)

The final step takes the top refined text chunks and passes them to the LLM with an aggressive `temperature=0.0` System Prompt.

**Strict Mandates:**
1. **Zero Hallucination:** "I cannot find sufficient evidence" is the required fallback.
2. **Comprehensive Synthesis:** The LLM must synthesize the diverse chunks, not just summarize the first article.
3. **Traceable Citations:** Every claim MUST be backed by an inline, Harvard-style citation explicitly including the `[PMID: XXXXXX]`.

---

# ☁️ Next Steps: Cloud & User Interface

Our backend AI engine is complete and hardened.

**Phase 5: Cloud Migration**
- Move local ChromaDB to a managed cloud vector database (e.g., Pinecone or Qdrant).
- Wrap the Python pipeline in **FastAPI** to expose `/query` and `/chat` endpoints.

**Phase 6: Frontend Development**
- Build an **Angular** Web Application.
- Implement session-based chat UI using the FastAPI endpoints.
- Deploy UI and API servers via Docker.

---

# 💡 Open Discussion & Questions

### Thank You

- Thoughts on the Multi-Agent Flow?
- Front-End UX considerations?
- Suggestions for additional Metadata tracking (e.g., Journal Impact Factor)?
