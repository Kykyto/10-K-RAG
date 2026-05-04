# app.py
import streamlit as st

# --- Page config (must be first st. call) ---
st.set_page_config(
    page_title="SEC 10-K RAG",
    page_icon="📊",
    layout="wide",
)

st.title("📊 SEC 10-K RAG Chatbot")
st.caption("Ask questions about company filings — powered by RAG over SEC EDGAR data")

with st.sidebar:
    st.header("Data Ingestion")
    
    tickers_input = st.text_input(
        "Tickers (comma-separated)",
        value="NVDA, AAPL, MSFT",
    )
    
    if st.button("Ingest Filings", type="primary", use_container_width=True):
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        
        if tickers:
            # st.spinner shows a loading indicator while the block runs
            with st.spinner(f"Fetching {', '.join(tickers)}..."):
                for ticker in tickers:
                    # Use your existing functions here
                    st.write(f"Fetching {ticker}...")
                    text = fetch_10k(ticker)
                    
                    if text:
                        chunks = chunk_10k(text, ticker)
                        # ... your existing embed + upsert logic
                        st.write(f"  ✓ {ticker}: {len(chunks)} chunks indexed")
                    else:
                        st.warning(f"  ✗ {ticker}: no valid 10-K found")
            
            st.success("Ingestion complete!")
        else:
            st.warning("Enter at least one ticker.")
    
    st.divider()
    st.header("Index Stats")
    st.metric("Total chunks", collection.count())

# Initialize chat history (persists across reruns)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display all previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Show sources in a collapsible section
        if msg.get("sources"):
            with st.expander("📄 Sources"):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(
                        f"**[{i}]** {src['ticker']} — Item {src['item']}: "
                        f"{src['section']} (score: {src['score']:.3f})"
                    )

# Chat input
if prompt := st.chat_input("Ask about SEC filings..."):
    # 1. Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching filings..."):
            # Your existing smart_search
            chunks = smart_search(prompt)
        
        with st.spinner("Generating answer..."):
            prompt_text = build_prompt(prompt, chunks)
            
            # Call Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:3b",
                    "prompt": prompt_text,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_ctx": 4096},
                },
                timeout=120,
            )
            answer = response.json()["response"]
        
        # Display the answer
        st.markdown(answer)
        
        # Display sources
        sources_data = []
        if chunks:
            with st.expander("📄 Sources"):
                for i, c in enumerate(chunks, 1):
                    st.markdown(
                        f"**[{i}]** {c['ticker']} — Item {c['item']}: "
                        f"{c['section']} (score: {c['score']:.3f})"
                    )
                    sources_data.append(c)
    
    # 3. Save to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources_data,
    })