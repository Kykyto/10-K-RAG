# 📊 10-K RAG — Ask Questions About SEC Filings

A Retrieval-Augmented Generation (RAG) system that lets you chat with SEC 10-K filings using natural language. Built from scratch — no LangChain, no abstractions — to understand every layer of the RAG pipeline.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![ChromaDB](https://img.shields.io/badge/Vector_Store-ChromaDB-orange)
![Ollama](https://img.shields.io/badge/LLM-Ollama-green)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)

## Demo

```
> What are NVIDIA's main risk factors?

NVIDIA faces several significant risks:
- Export controls have already and may in the future encourage customers
  to "design-out" U.S. semiconductors from their products [Source 4]
- Dependency on third-party suppliers reduces control over product quantity,
  quality, and delivery schedules [Source 5]
- The use of GPUs for mercurial applications like cryptocurrency mining
  has led to inconsistent demand spikes [Source 3]
```

## How It Works

```
SEC EDGAR API ─→ Section-Aware Chunking ─→ Embeddings ─→ ChromaDB
                                                              │
User Question ─→ Smart Router ─→ Hybrid Retrieval ───────────→│
                                         │
                                   Ranked Chunks ─→ LLM ─→ Cited Answer
```

**1. Ingestion** — Fetches 10-K filings directly from SEC EDGAR via the `edgartools` library. Validates that filings are complete (not 10-K/A amendments) and contain core sections (Items 1, 1A, 7) before indexing.

**2. Section-Aware Chunking** — Instead of naive fixed-size splitting, the chunker first detects 10-K Item boundaries (Risk Factors, MD&A, Business, etc.) then splits within each section using paragraph-aware token windowing with overlap. Each chunk carries its section metadata.

**3. Embedding & Storage** — Chunks are embedded with `bge-small-en-v1.5` (384-dim, runs on CPU) and stored in ChromaDB with metadata indexing for fast filtered search.

**4. Smart Retrieval** — A query router detects whether the question targets a single company, compares multiple companies, or is a broad search. For comparisons, it retrieves equal chunks per company to avoid embedding bias toward verbose filers. Metadata filtering scopes search to specific tickers or sections.

**5. Generation** — Retrieved chunks are injected into a citation-aware prompt. The LLM is constrained to answer only from provided sources and cite them using `[Source N]` notation.

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) with a model pulled (e.g. `ollama pull qwen2.5:3b`)

### Setup

```bash
git clone https://github.com/Kykyto/10-K-RAG.git
cd 10-K-RAG

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env if needed (defaults work with Ollama)
```

### Ingest Filings

```bash
python main.py
```

This fetches 10-K filings for the configured tickers from SEC EDGAR, chunks them, and stores the embeddings in ChromaDB.

### Chat

```bash
streamlit run app.py
```

### Example Queries

| Query | What it tests |
|-------|---------------|
| "What are NVIDIA's main risk factors?" | Single-company retrieval + Item 1A filtering |
| "Compare the revenue models of Apple and Microsoft" | Multi-company balanced retrieval |
| "What is Tesla's dividend policy?" | Precise fact lookup (Item 5) |
| "Which companies mention AI as a risk factor?" | Cross-company broad search |

## Architecture

```
10-K-RAG/
├── app.py                  # Streamlit chat interface
├── main.py                 # Ingestion entry point
├── config.py               # All settings via .env
├── notebook.ipynb           # Development / exploration notebook
├── App/
│   ├── database.py         # ChromaDB wrapper (store, query, metadata filtering)
│   └── rag.py              # Retrieval + prompt building + LLM generation
├── Scripts/
│   └── ingestion.py        # SEC EDGAR client + section-aware chunker
└── .env.example            # Configuration template
```

## Configuration

All settings are in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Ollama API endpoint |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Model name (try `mistral:7b` for better quality) |
| `CHUNK_SIZE` | `400` | Tokens per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between consecutive chunks |
| `TEMPERATURE` | `0.1` | LLM temperature (low = more factual) |
| `DB_PATH` | `./chroma_db` | ChromaDB storage path |

To use a cloud LLM instead of Ollama, set `LLM_PROVIDER=anthropic` and add your `ANTHROPIC_API_KEY`.

## Design Decisions

**Why no LangChain?** — This project was built to understand RAG from the ground up. Every component (chunking, embedding, retrieval, routing, prompting) is implemented explicitly so the logic is readable and debuggable.

**Why section-aware chunking?** — 10-K filings have a standardized structure (Items 1-15). Naive chunking creates chunks that straddle section boundaries, mixing risk factors with revenue discussion. Section-aware chunking guarantees each chunk belongs to exactly one section, which improves both retrieval precision and LLM output quality.

**Why a query router?** — Pure vector search is biased toward companies with more verbose filings. When comparing Apple vs Microsoft, unrouted search returns 7 MSFT chunks and 1 AAPL chunk. The router detects comparison queries and enforces balanced retrieval per company.

**Why metadata filtering?** — Embedding similarity alone can't distinguish "NVIDIA mentions risk" from "a competitor mentions NVIDIA as a risk." Metadata filtering on ticker + section eliminates this ambiguity before the vector search runs.

## Limitations & Future Work

- **No table parsing** — Financial tables in 10-K filings are extracted as raw text, losing structure. Libraries like `camelot` or `unstructured` could improve this.
- **No cross-encoder reranking** — The current reranking is heuristic-based. A cross-encoder (e.g. `ms-marco-MiniLM`) would improve precision.
- **No evaluation framework** — Adding RAGAS or a manual eval set would quantify retrieval and generation quality.
- **Single filing type** — Currently handles 10-K only. Extending to 10-Q and earnings transcripts would increase coverage.

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Embeddings | [bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) | 33M params, runs on CPU, strong retrieval benchmarks |
| Vector Store | [ChromaDB](https://www.trychroma.com/) | Local, persistent, supports metadata filtering |
| LLM | [Ollama](https://ollama.ai/) (Qwen 2.5 3B) | Runs on laptop, no API key needed |
| Data Source | [SEC EDGAR](https://www.sec.gov/edgar) | Free, official, no API key needed |
| UI | [Streamlit](https://streamlit.io/) | Minimal code for a functional chat interface |