from Scripts.ingestion import get_10ks
from Scripts.chunking import chunk_10k
from Scripts.database import *
from Scripts.prompt import ask
from Scripts.config import *


TICKERS = ['AAPL', 'GOOG', 'MSFT', 'TSLA', 'META', 'NVDA', 'NFLX']


if __name__ == "__main__":
    # Step 1: Fetch 10-K filings for the specified tickers
    ten_ks = get_10ks(TICKERS)
    for ticker, ten_k in ten_ks.items():
        print(f"{ticker} 10-K length: {len(ten_k)} characters")

    # Step 2: Chunk the 10-K filings and prepare metadata
    all_chunks = []
    all_metadata = []
    for ticker, text in ten_ks.items():
        chunks = chunk_10k(text, ticker)
        texts = [c["text"] for c in chunks]
        
        for chunk in chunks:
            all_chunks.append(chunk["text"])
            all_metadata.append(chunk["metadata"])
    
    print(f"Total chunks created: {len(all_chunks)}")
    if all_metadata:
        print("Example metadata for the first chunk:")
        print(all_metadata[0])

    # Step 3: Insert chunks into the ChromaDB collection
    collection = create_or_get_collection(DB_PATH, COLLECTION_NAME)
    insert_or_update_chunks(collection, all_chunks, all_metadata)

    # Step 4: Example query
    query = "What are the main risk factors mentioned in Apple's 10-K?"
    answer = ask(query, top_k=5, where={"ticker": "AAPL"})
    print("\nANSWER:")
    print(answer)



