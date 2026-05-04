from .database import *
import requests


def build_prompt(query: str, retrieved_chunks: list[dict]) -> str:
    """
    Build the full prompt with retrieved context.
    
    Why this structure?
    - System-level instructions set the behavior (cite sources, don't hallucinate)
    - Each source is labeled [Source N] so the LLM can reference them
    - The question comes AFTER the context, so the model reads the sources
      before it sees what to do with them (this matters for small models)
    """
    # Format each chunk as a labeled source
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        header = f"[Source {i}] {chunk['ticker']} — Item {chunk['item']}: {chunk['section']}"
        context_parts.append(f"{header}\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    prompt = f"""You are a financial analyst assistant. Answer the question based ONLY on the provided sources from SEC 10-K filings.

Rules:
- Use ONLY information from the sources below. Do not use prior knowledge.
- Cite your sources using [Source N] when making a claim.
- If the sources don't contain enough information, say so explicitly.
- Be precise with financial figures and time periods.
- Do not generate URLs or links. Source citations use [Source N] format only.
CRITICAL: If a source does not contain specific information, do NOT fill in gaps 
from your own knowledge. Say "the sources do not provide details on X" instead.
Only state facts that you can directly tie to a [Source N].

Sources:
{context}

Question: {query}

Answer with citations:"""
    
    return prompt


def ask(query: str, top_k: int = 5, where: dict = None) -> str:
    """
    End-to-end RAG: retrieve → build prompt → generate.
    """
    # Step 1: Retrieve
    collection = create_or_get_collection('./chroma_db', 'sec_10k')
    chunks = search(collection,query, top_k=top_k, where=where)
    
    # Step 2: Build prompt
    prompt = build_prompt(query, chunks)
    
    # Step 3: Call Ollama
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:3b",   # adjust to your installed model
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,   # low = more factual, less creative
                "num_ctx": 4096,      # context window size
            },
        },
        timeout=240,
    )
    response.raise_for_status()
    answer = response.json()["response"]
    
    return answer