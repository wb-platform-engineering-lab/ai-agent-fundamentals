"""
memory.py — ChromaDB layer for doc-oracle.

Responsibilities:
  1. Ingest: read docs → chunk → embed → store
  2. Search: embed query → find nearest chunks → return with sources

Run directly to ingest documents:
  python memory.py --ingest docs/
  python memory.py --search "how to rollback a deploy"
"""

import argparse
import re
from pathlib import Path

import chromadb

COLLECTION_NAME = "doc-oracle"
CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 50     # overlap between consecutive chunks


def get_collection() -> chromadb.Collection:
    """Get or create the ChromaDB collection. Stored locally in ./chroma_data/"""
    client = chromadb.PersistentClient(path="./chroma_data")
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # cosine similarity
    )


def split_into_chunks(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks.

    Why overlap? So sentences that fall at a chunk boundary
    are captured by both the previous and next chunk.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += size - overlap
    return chunks


def ingest_docs(folder: str):
    """Read all .md and .txt files in folder and store in ChromaDB."""
    collection = get_collection()
    folder_path = Path(folder)
    files = list(folder_path.glob("**/*.md")) + list(folder_path.glob("**/*.txt"))

    if not files:
        print(f"No .md or .txt files found in {folder}")
        return

    total_chunks = 0
    for file in files:
        text = file.read_text(encoding="utf-8")
        chunks = split_into_chunks(text)

        # Build IDs, documents, and metadata for each chunk
        ids = [f"{file.stem}-chunk{i}" for i in range(len(chunks))]
        metadatas = [{"source": str(file), "chunk_index": i} for i in range(len(chunks))]

        # Upsert — safe to re-run, will overwrite existing chunks
        collection.upsert(documents=chunks, metadatas=metadatas, ids=ids)

        print(f"  ✔ {file.name} → {len(chunks)} chunks")
        total_chunks += len(chunks)

    print(f"\nIngested {len(files)} files, {total_chunks} total chunks.")
    print("Ready to query.")


def search(query: str, k: int = 3) -> list[dict]:
    """
    Find the K most relevant chunks for a query.

    Returns a list of dicts with:
      - text: the chunk content
      - source: the file it came from
      - score: relevance score (0–1, higher is better)
    """
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []

    k = min(k, count)
    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "score": round(1 - dist, 3),  # convert distance to similarity
        })
    return chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="doc-oracle memory layer")
    parser.add_argument("--ingest", metavar="FOLDER", help="Ingest docs from folder")
    parser.add_argument("--search", metavar="QUERY", help="Search the vector store")
    parser.add_argument("-k", type=int, default=3, help="Number of results (default: 3)")
    args = parser.parse_args()

    if args.ingest:
        ingest_docs(args.ingest)
    elif args.search:
        results = search(args.search, k=args.k)
        if not results:
            print("No results. Run: python memory.py --ingest docs/")
        for r in results:
            print(f"\n[score: {r['score']}] {r['source']}")
            print(r["text"][:300] + "...")
    else:
        parser.print_help()
