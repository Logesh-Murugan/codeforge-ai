"""
Text chunking utilities for the RAG pipeline.

Splits long documents into overlapping fixed-size chunks before
embedding, improving retrieval precision for large agent outputs.
"""
from __future__ import annotations

from typing import List

from memory.schemas import TextChunk


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100,
    artifact_type: str = "",
) -> List[TextChunk]:
    """
    Split *text* into overlapping character-based chunks.

    Args:
        text:          Input text to split.
        chunk_size:    Maximum character length per chunk.
        overlap:       Number of characters shared between consecutive chunks.
        artifact_type: Source label attached to each chunk's metadata.

    Returns:
        List of :class:`TextChunk` objects in order.  Returns a single
        chunk equal to *text* when ``len(text) <= chunk_size``.
    """
    if not text:
        return []

    if len(text) <= chunk_size:
        return [
            TextChunk(
                chunk_index=0,
                content=text,
                char_start=0,
                char_end=len(text),
                source_artifact_type=artifact_type,
            )
        ]

    step = max(1, chunk_size - overlap)
    chunks: List[TextChunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(
            TextChunk(
                chunk_index=index,
                content=text[start:end],
                char_start=start,
                char_end=end,
                source_artifact_type=artifact_type,
            )
        )
        if end == len(text):
            break
        start += step
        index += 1

    return chunks


def chunk_documents(
    texts: List[str],
    chunk_size: int = 800,
    overlap: int = 100,
    artifact_types: List[str] | None = None,
) -> List[TextChunk]:
    """
    Chunk a list of documents and return a flat list of :class:`TextChunk`.

    Args:
        texts:          Documents to chunk.
        chunk_size:     Characters per chunk.
        overlap:        Character overlap.
        artifact_types: Optional list of artifact labels, one per document.

    Returns:
        Flat list of all chunks across all documents.
    """
    all_chunks: List[TextChunk] = []
    for i, text in enumerate(texts):
        atype = (artifact_types[i] if artifact_types and i < len(artifact_types) else "")
        all_chunks.extend(
            chunk_text(text, chunk_size=chunk_size, overlap=overlap, artifact_type=atype)
        )
    return all_chunks
