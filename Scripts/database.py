from .config import *
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import hashlib


def create_or_get_collection(path=DB_PATH, collection_name=COLLECTION_NAME):
    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-en-v1.5",
        device="cpu",
    )

    # PersistentClient = saves to disk automatically
    client = chromadb.PersistentClient(path=path)

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"Collection has {collection.count()} documents")
    return collection


def insert_or_update_chunks(collection, all_chunks, all_metadata):
    ids = []
    documents = []
    metadatas = []

    for i, (chunk_text, metadata) in enumerate(zip(all_chunks, all_metadata)):
        chunk_id = hashlib.md5(
            f"{metadata['ticker']}_{metadata['item']}_{i}_{chunk_text[:100]}".encode()
        ).hexdigest()
        
        ids.append(chunk_id)
        documents.append(chunk_text)
        metadatas.append({
            "ticker": metadata["ticker"],
            "item": metadata["item"],
            "section_title": metadata["section_title"],
            "chunk_index": metadata["chunk_index"],
            "token_count": metadata["token_count"],
        })

    batch_size = 500
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
        )

    print(f"Stored {collection.count()} chunks")


def search(collection,query: str, top_k: int = 5, where: dict = None) -> list[dict]:
    kwargs = {
        "query_texts": [query],      # ChromaDB embeds this for you
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    
    results = collection.query(**kwargs)
    
    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "text": doc,
            "ticker": meta["ticker"],
            "section": meta["section_title"],
            "item": meta["item"],
            "score": 1 - dist,
        })
    
    return output