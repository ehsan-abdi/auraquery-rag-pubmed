---
marp: true
theme: default
class: default
paginate: true
backgroundColor: "#f8f9fa"
style: |
  section {
    font-family: 'Inter', 'Helvetica Neue', sans-serif;
    font-size: 22px; 
    color: #333;
  }
  h1 { color: #1a5f7a; font-size: 2.2em; margin-bottom: 0.2em; border-bottom: 3px solid #e05e5e; padding-bottom: 10px;}
  h2 { color: #227c9d; font-size: 1.5em; margin-top: 0; }
  h3 { color: #e05e5e; font-size: 1.2em; }
  .highlight { background-color: #fff3cd; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
  
  /* Flexbox Layouts for Visual Contrast */
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  
  /* Pros & Cons Boxes */
  .pro-box { background: #e8f5e9; padding: 15px; border-radius: 12px; border-left: 6px solid #4caf50; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
  .con-box { background: #ffebee; padding: 15px; border-radius: 12px; border-left: 6px solid #f44336; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
  .info-box { background: #e3f2fd; padding: 15px; border-radius: 12px; border-left: 6px solid #2196f3; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
  
  /* Tables */
  table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden; }
  th { background-color: #1a5f7a; color: white; padding: 10px; text-align: left; font-size: 1.0em; }
  td { padding: 10px; border-bottom: 1px solid #eee; background: white; font-size: 0.9em; }
  tr:last-child td { border-bottom: none; }
  
  /* Callouts & Badges */
  .badge { background: #227c9d; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.7em; text-transform: uppercase; letter-spacing: 1px; }
  .badge-alt { background: #e05e5e; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.7em; text-transform: uppercase; }
  
  /* Flowchart Stages */
  .flow-container { display: flex; flex-direction: column; align-items: center; gap: 4px; font-size: 0.82em; margin: 10px 0; }
  .flow-grid { display: grid; grid-template-columns: 1fr 1fr; width: 100%; gap: 15px; align-items: start; }
  .flow-col { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; }
  .flow-box { padding: 8px; border-radius: 8px; width: 85%; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
  .flow-box-1 { background: #e3f2fd; border: 2px solid #2196f3; }
  .flow-box-2 { background: #f3e5f5; border: 2px solid #9c27b0; width: 90%; }
  .flow-box-3 { background: #fff3cd; border: 2px solid #ffc107; }
  .flow-box-4 { background: #e8f5e9; border: 2px solid #4caf50; }
  .flow-box-fallback { background: #ffebee; border: 2px dashed #f44336; width: 85%; padding: 6px; }
  .flow-arrow { font-size: 1.2em; font-weight: bold; margin: -2px 0; }
  .flow-title { font-weight: bold; font-size: 1.05em; display: block; margin-bottom: 2px; }
  .flow-sub { font-size: 0.9em; color: #555; line-height: 1.2; display: block; }
  
  /* Code and Pre */
  pre { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 10px; font-size: 0.85em; overflow-x: auto; box-shadow: inset 0 0 10px rgba(0,0,0,0.5); }
---

<!-- _class: lead -->
# Formulating Dr. Aura 🧬
## An End-to-End Walkthrough of RAG Engineering over PubMed

**Ehsan Abdi**
**26 February 2026**

---

# 1. Navigating the PubMed Database

*Building a RAG on a medical database introduces specific architectural and data processing considerations compared to standard document retrieval.*

<div class="grid-2">
  <div class="info-box">
    <h3>🔍 Inherent Characteristics</h3>
    <ul>
      <li><strong>Structural Variance:</strong> XML schemas often contain extraneous elements like references, formulas, and supplementary data that require rigorous parsing.</li>
      <li><strong>Information Overload:</strong> Simple vector searches may return highly-cited generic review articles rather than specific, applicable clinical trials.</li>
    </ul>
  </div>
  
  <div class="pro-box" style="border-left-color: #9c27b0; background: #f3e5f5;">
    <h3>🎓 The RAG Learning Opportunity</h3>
    <p>By utilizing the PubMed Open Access subset, the following competencies were developed:</p>
    <ul>
      <li>Advanced XML parsing and data harmonization.</li>
      <li>Investigating semantic chunking tailored for scientific literature.</li>
      <li>Developing precision-focused multi-stage retrieval pipelines.</li>
    </ul>
  </div>
</div>

---

# 2. Data Ingestion & Preprocessing

<div class="info-box" style="margin-bottom: 20px">
  <strong>The Dataset:</strong> Focused exclusively on Open-Access PMC articles retrieved via the Biopython Entrez API.
</div>

### The "Two-Tier JSON" Strategy 
To optimize retrieval efficiency, the ingested data was split into two discrete indices.

<div class="grid-2">
  <div>
    <strong>Tier 1 JSON: Abstract + Metadata</strong>
    <p><em>Utilized for fast, broad semantic filtering to establish relevance.</em></p>
  </div>
  <div>
    <strong>Tier 2 JSON: Full-Text + Metadata</strong>
    <p><em>Utilized for deep-dive paragraph extraction once relevant papers are identified.</em></p>
  </div>
</div>

### ✨ Data Transformation
- **Metadata Preservation:** Maintained *MeSH Keywords* and *Publication Type* to enable rigid filtering during retrieval.
- **Recursive Indicators:** Stripped non-essential XML tags and applied markdown indicators (`##`) to demarcate section headers (e.g., `## Introduction`).

---

# 3. Chunking Strategy

<div class="grid-2">
  <div>
    <h3>Semantic Chunking Method</h3>
    <p>Documents were parsed natively using the structural headers (<code>##</code>) established during ingestion.</p>
    <ul>
      <li><strong>Abstracts:</strong> Maintained as a single, holistic chunk.</li>
      <li><strong>Full-Text:</strong> Chunked strictly per section (e.g., Methods vs. Results).</li>
      <li><strong>Length Control:</strong> If a section exceeded the optimal length, a fallback of <strong>1000 max-tokens with a 200-token overlap</strong> was applied.</li>
    </ul>
  </div>
  <div class="info-box">
    <h3>Index Size Comparison</h3>
    <p>Each chunk inherited the parent document's metadata, alongside an added <code>section_name</code> field.</p>
    <table>
      <tr>
        <th>Index Layer</th>
        <th>Item Count</th>
      </tr>
      <tr>
        <td><strong>Index A</strong> (Abstracts)</td>
        <td>~888 documents</td>
      </tr>
      <tr>
        <td><strong>Index B</strong> (Body Chunks)</td>
        <td>~16,972 chunks</td>
      </tr>
    </table>
  </div>
</div>

---

# 4. Choosing the Embedding Model

*Translating complex biomedicine into mathematical vector representations.*

| Model Option | Type | Clinical Reasoning | Cost / Accessibility |
| :--- | :--- | :--- | :--- |
| **OpenAI `text-emb-3-small`** | Dense | Offers strong general semantic understanding, though may exhibit slightly lower precision on rare acronyms. | Highly cost-effective and accessible. |
| **ColBERT (v2)** | Sparse / Late-Interaction | Phenomenal at exact clinical keyword matching and syntax. | Computationally intensive with significant vector storage requirements. |

<div class="pro-box" style="font-size: 0.75em; padding: 10px; margin-top: 5px;">
  <h3 style="margin-top: 0; margin-bottom: 2px;">🏆 The Choice: OpenAI</h3>
  <p style="margin: 0; line-height: 1.3;">For the scope of this project, OpenAI was prioritized for its balance of performance and efficiency. For a production-grade enterprise application, ColBERT represents a strong potential upgrade path.</p>
</div>

---

# 5. The Vector Database Deployment

Initial phase development commenced with a localized **ChromaDB** instance before transitioning to cloud infrastructure.

<div class="grid-2">
  <div class="pro-box">
    <h3>Advantages of Local DB</h3>
    <ul>
      <li>Zero infrastructure cost and immediate setup.</li>
      <li>Operates entirely within the Python runtime environment.</li>
      <li>Ideal for rapid prototyping and offline algorithmic development.</li>
    </ul>
  </div>
  <div class="con-box">
    <h3>Limitations Encountered</h3>
    <ul>
      <li><strong>No Native Hybrid Search:</strong> Out-of-the-box, ChromaDB lacked combined dense vector and BM25 keyword search functionality.</li>
      <li>Because medical queries require exact keyword matching, a manual two-stage Python process had to be engineered.</li>
    </ul>
    <p><em>This major limitation ultimately necessitated the migration to a more advanced vector database architecture.</em></p>
  </div>
</div>

---

# 6. Two-Stage Semantic Retrieval Strategy

*The core retrieval engine utilizes a Multi-Stage Filtering approach through LangChain and Qdrant.*

<div class="flow-container">
  <div class="flow-box flow-box-1">
    <span class="flow-title" style="color: #1a5f7a;">Stage 1: Index A (Abstract Search)</span>
    <span class="flow-sub">Dense vector search over abstracts to isolate relevant Candidate PMIDs</span>
  </div>
  <div class="flow-grid">
    <div class="flow-col">
      <div class="flow-arrow" style="color: #2196f3;">⬇</div>
      <div class="flow-box flow-box-2">
        <span class="flow-title" style="color: #7b1fa2;">Stage 2: Index B (Full-Text)</span>
        <span class="flow-sub">Semantic search restricted <em>only</em> to the Candidate PMIDs' chunks</span>
      </div>
    </div>
    <div class="flow-col">
      <div class="flow-arrow" style="color: #f44336; font-size: 0.8em;"><em>Fallback Route</em> ⬇</div>
      <div class="flow-box flow-box-fallback">
        <span class="flow-title" style="color: #c62828; font-size: 0.9em;">Global Index B Search</span>
        <span class="flow-sub" style="font-size: 0.85em;">Triggered if explicitly requested or Phase 1 fails</span>
      </div>
    </div>
  </div>
  <div class="flow-arrow" style="color: #9c27b0;">⬇</div>
  <div class="flow-box flow-box-3">
    <span class="flow-title" style="color: #b28900;">Stage 3: Custom Reranking</span>
    <span class="flow-sub">Algorithmic boosts applied for Evidence Quality (RCTs), Recency, and Section Relevance</span>
  </div>
  <div class="flow-arrow" style="color: #ffc107;">⬇</div>
  <div class="flow-box flow-box-4">
    <span class="flow-title" style="color: #2e7d32;">Stage 4: Diversity Control</span>
    <span class="flow-sub">Hard-cap applied to limit maximum allowable chunks per PMID</span>
  </div>
</div>

---

# 7. Reranking and Diversity Filtering

Raw vector similarity scores alone were insufficient; custom programmatic logic was introduced.

<div class="grid-2">
  <div class="info-box">
    <h3>⚖️ Custom Reranking Algorithm</h3>
    <p>Metadata was utilized to deterministically adjust vector similarity scores:</p>
    <ul>
      <li><strong>Publication Quality:</strong> +RCTs and Meta-Analyses over general reviews or case studies.</li>
      <li><strong>Section Relevance:</strong> Boosts applied to chunks originating from "Results" and "Conclusion" sections.</li>
      <li><strong>Recency Function:</strong> Applied exponential decay based on publication year.</li>
    </ul>
  </div>
  <div class="pro-box" style="border-left-color: #ff9800; background: #fff3e0;">
    <h3>🛡️ Diversity Enforcement</h3>
    <p>A maximum constraint was established, capping retrieval to <strong>5 chunks per Article</strong>.</p>
    <p>This enforces multi-document synthesis by preventing a single extensive review paper from monopolizing the final LLM context window.</p>
  </div>
</div>

---

# 8. Conversational Memory & Dual Prompting

*Introducing chat history complicates standard RAG retrieval (e.g., resolving pronouns).*

### Strategy: Two-Level Prompt Engineering

1. **The Interceptor (Chat History Parser):**
   *Role:* An LLM is tasked with reading the chat history, resolving pronouns, and extracting explicit identifiers.
   *Example:* User: *"What is the standard dosage?"* ➔ Interceptor: *"What is the standard dosage for Bevacizumab? PMID: 1234567"*

2. **The Metadata Extractor:**
   *Role:* Employs Pydantic models to parse the updated query and isolate structured metadata filters.
   *Example:* *"Show me recent trials"* ➔ Extracted Filter: `{ "year": 2024, "type": "RCT" }`

**System Prompt Constraints:** Prompts were designed to strictly bound the LLM to the provided context, requiring an admission of insufficient data if the answer was absent.

---

# 9. Answer Generation Strategy

Following context assembly, a generative model synthezises the final response.

### The LLM Selection: `gpt-4o-mini`
- It provides rapid inference times, is highly cost-effective, and maintains sophisticated instruction-following capabilities relative to its parameter size.

<div class="grid-2" style="margin-top: 20px;">
  <div class="con-box" style="background:#f4f4f4; border-left-color: #555;">
    <strong>Temperature Specification (0.0)</strong><br>
    In biomedical contexts, variance and creativity equate to hallucination risk. Setting the temperature to 0.0 enforces deterministic outputs, anchoring the LLM strictly to the provided evidentiary chunks.
  </div>
  <div class="con-box" style="background:#f4f4f4; border-left-color: #555;">
    <strong>Top-p Parameter (1.0)</strong><br>
    Given the temperature freeze at 0.0, the model exclusively selects the highest probability token, rendering adjustments to the Top-p parameter redundant.
  </div>
</div>

---

# 10. The Complete System Architecture

<div style="text-align: center; margin: 10px 0px;">
  <img src="https://mermaid.ink/svg/Zmxvd2NoYXJ0IFRECiAgICBRKFsiVXNlciBRdWVyeSJdKSAtLT4gTVsiQ2hhdCBIaXN0b3J5IEludGVyY2VwdG9yIExMTSJdCiAgICBNIC0tPiBIeXsiVHdvLVN0YWdlIFNlYXJjaCBQaXBlbGluZSJ9CiAgICAKICAgIHN1YmdyYXBoICJRZHJhbnQgQ2xvdWQgREIiCiAgICAgICAgSHkgLS4tPnwiU3RhZ2UgMSJ8IEFbKCJJbmRleCBBIChBYnN0cmFjdHMpIildCiAgICAgICAgQSAtLi0+fCJDYW5kaWRhdGUgUE1JRHMifCBIeQogICAgICAgIEh5IC0uLT58IlN0YWdlIDIifCBCWygiSW5kZXggQiAoQm9keSBDaHVua3MpIildCiAgICBlbmQKICAgIAogICAgQiAtLT4gQ1siQWdncmVnYXRvciAmIEN1c3RvbSBSZXJhbmtlciJdCiAgICBDIC0tPnwiQm9vc3QgUkNUcyAvIExpbWl0IGNodW5rcyBwZXIgcGFwZXIifCBEWyJUb3AgSyBEaXZlcnNlIENodW5rcyJdCiAgICAKICAgIEQgLS0+IFNbIlN5c3RlbSBQcm9tcHQgSW5qZWN0aW9uIl0KICAgIFMgLS0+IEdbImdwdC00by1taW5pIEdlbmVyYXRvciJdCiAgICBHIC0tPiBSKFsiRmluYWwgTWVkaWNhbCBSZXNwb25zZSJdKQogICAgCiAgICBzdHlsZSBNIGZpbGw6I2UzZjJmZDsKICAgIHN0eWxlIEIgZmlsbDojZjNlNWY1LHN0cm9rZTojOWMyN2IwOwogICAgc3R5bGUgQyBmaWxsOiNmZmYzY2Q7CiAgICBzdHlsZSBHIGZpbGw6I2U4ZjVlOTsKICAgIHN0eWxlIEEgZmlsbDojZjNlNWY1LHN0cm9rZTojOWMyN2IwOw==" alt="System Architecture" width="17%">
</div>

---

# 11. Evaluation: Dual LLM-as-a-Judge

*Quantitative validation was conducted via an autonomous evaluation framework leveraging two separate GenAI models to prevent bias.*

<div class="grid-2">
  <div>
    <div style="text-align: center;">
      <img src="https://mermaid.ink/svg/Z3JhcGggVEQKICAgIEFbIlJhdyBBcnRpY2xlIFRleHQiXSAtLT4gQlsiUUEgR2VuZXJhdG9yIExMTSAoZ3B0LTRvKSJdCiAgICBCIC0tPiBDWyJTdGF0aWMgUUEgVGVzdCBCYW5rIl0KICAgIEMgLS0+fCJRdWVzdGlvbnMifCBEWyJBdXJhIFF1ZXJ5IEVuZ2luZSJdCiAgICBEIC0tPnwiU3lzdGVtIEFuc3dlciJ8IEV7Ikp1ZGdlIExMTSAoZ3B0LTRvKSJ9CiAgICBDIC0tPnwiR3JvdW5kIFRydXRoInwgRQogICAgRSAtLT58IjAtNSBTY29yZSJ8IEZbIkdyb3VuZGVkbmVzcyBNZXRyaWMiXQogICAgRSAtLT58IjAtNSBTY29yZSJ8IEdbIkhlbHBmdWxuZXNzIE1ldHJpYyJd" alt="Evaluation Framework" width="30%">
    </div>
  </div>
  <div>
    <h3>The Asynchronous Framework</h3>
    <ul>
      <li><strong>Step 1 (Generation):</strong> An LLM extracts ground-truth facts from chunks and generates structurally diverse questions into a static test bank JSON.</li>
      <li><strong>Step 2 (Execution):</strong> The Aura pipeline retrieves context and generates an answer without knowledge of the ground truth.</li>
      <li><strong>Step 3 (Judging):</strong> A separate instance scores the final answer against the hidden ground truth.</li>
    </ul>
    <strong>Enhancement Pathways:</strong>
    1. <em>Ingestion:</em> Expansion beyond open-access limitations.
    2. <em>Retrieval:</em> Investigation into late-interaction models.
  </div>
</div>

---

# 12. Cloud Migration: Entering Production

The system transitioned from a local ChromaDB instance to a managed **Qdrant Cloud** database.

| Vector DB Option | Advantages | Disadvantages | Verdict |
| :--- | :--- | :--- | :--- |
| **Qdrant Cloud** | High-performance Rust-based architecture, native `MatchAny` payload schema support, zero local state dependency. | Minor integration adjustments required for LangChain compatibility. | 🏆 **Selected.** Resolved local scalability constraints. |
| **Pinecone** | Industry standard, robust APIs. | Proprietary nature and restrictive free-tier limitations. | Not prioritised for this phase. |
| **Milvus** | Exceptional scalability for massive datasets. | High deployment complexity overhead. | Deemed excessive for current architecture scale. |

*This migration significantly reduced inference latency and decoupled the data layer from the application compute environment.*

---

# 13. Frontend & Containerization

<div class="grid-2">
  <div>
    <h3>Deployment Infrastructure</h3>
    <ul>
      <li><strong>Frontend Interface:</strong> Designed around a modern chat-based UI using frameworks applicable for stateful conversations.</li>
      <li><strong>Backend Excision:</strong> The retrieval engine was decoupled and exposed via a robust <strong>FastAPI</strong> REST endpoint.</li>
      <li><strong>Containerization:</strong> The application environments were encapsulated within <strong>Docker containers</strong> to guarantee environment parity across deployments.</li>
    </ul>
  </div>
  <div style="text-align: center;">
    <div style="border: 4px solid #227c9d; border-radius: 12px; height: 280px; display: flex; align-items: center; justify-content: center; background: #e3f2fd; color: #1a5f7a;">
      <div>
        <h3>🩺 Dr. Aura UI Placeholder</h3>
        <p><em>[Insert Application Screenshot Here]</em></p>
        <hr style="border-top:1px solid #1a5f7a; width: 50%; margin: 10px auto;">
        <p style="font-size: 0.6em; margin-bottom: 2px;">User: What are the genetic causes?</p>
        <p style="font-size: 0.6em">Dr. Aura: Based on ~3 retrieved papers...</p>
      </div>
    </div>
  </div>
</div>

---

<!-- _class: lead -->
# Thank You! 🚀

**Key Takeaway:**
*Building an effective RAG system over specialized medical literature demands meticulous architectural design across the Ingestion, Chunking, Retrieval, and Evaluation stages.*

![RAG Architecture Snapshot](/assets/rag_journey.png)
*(Image placeholder for architectural diagram or snapshot)*
