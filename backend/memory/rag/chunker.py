"""
ChunkingEngine — Phase 3.3 RAG Pipeline.

Provides four splitting strategies, configurable chunk size / overlap,
word-boundary awareness, and minimum-chunk filtering.

Strategies
----------
CHARACTER  — fixed-size character windows (fastest, default)
SENTENCE   — split on ``. ! ?`` boundaries, then window if still too large
PARAGRAPH  — split on blank lines first, then fall back to CHARACTER
RECURSIVE  — try PARAGRAPH → SENTENCE → CHARACTER (best quality)
"""
from __future__ import annotations

import hashlib
import re
import uuid
from typing import List, Optional

from memory.rag.schemas import ChunkRecord, ChunkingConfig, ChunkStrategy


# Sentence boundary pattern: end of sentence followed by whitespace or EOS.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
# Paragraph boundary: one or more blank lines.
_PARA_SPLIT = re.compile(r"\n{2,}")


class ChunkingEngine:
    """
    Full-featured chunking engine for the RAG ingestion pipeline.

    Args:
        config: A :class:`ChunkingConfig` instance.  When omitted the
                default config is used (CHARACTER, 800 chars, 100 overlap).
    """

    def __init__(self, config: Optional[ChunkingConfig] = None) -> None:
        self.config = config or ChunkingConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk(
        self,
        text: str,
        artifact_type: str = "",
        extra_metadata: Optional[dict] = None,
    ) -> List[ChunkRecord]:
        """
        Split *text* into :class:`ChunkRecord` objects.

        Args:
            text:           Input document text.
            artifact_type:  Label stored in each chunk's metadata.
            extra_metadata: Additional key/value pairs merged into each
                            chunk's ``metadata`` field.

        Returns:
            Ordered list of :class:`ChunkRecord`.  Empty list for blank input.
        """
        if not text or not text.strip():
            return []

        raw_chunks = self._split(text)
        records: List[ChunkRecord] = []
        total = len(raw_chunks)

        for idx, (content, char_start, char_end) in enumerate(raw_chunks):
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            metadata: dict = {
                "artifact_type": artifact_type,
                "chunk_index": idx,
                "total_chunks": total,
                "char_start": char_start,
                "char_end": char_end,
                "strategy": self.config.strategy.value,
            }
            if extra_metadata:
                metadata.update(extra_metadata)

            records.append(
                ChunkRecord(
                    chunk_id=str(uuid.uuid4()),
                    chunk_index=idx,
                    total_chunks=total,
                    content=content,
                    char_start=char_start,
                    char_end=char_end,
                    content_hash=content_hash,
                    source_artifact_type=artifact_type,
                    strategy=self.config.strategy,
                    metadata=metadata,
                )
            )

        return records

    def chunk_batch(
        self,
        texts: List[str],
        artifact_types: Optional[List[str]] = None,
        extra_metadata: Optional[dict] = None,
    ) -> List[List[ChunkRecord]]:
        """
        Chunk a list of documents.

        Returns:
            List-of-lists: one inner list per input document.
        """
        results: List[List[ChunkRecord]] = []
        for i, text in enumerate(texts):
            atype = artifact_types[i] if artifact_types and i < len(artifact_types) else ""
            results.append(self.chunk(text, artifact_type=atype, extra_metadata=extra_metadata))
        return results

    # ------------------------------------------------------------------
    # Strategy dispatching
    # ------------------------------------------------------------------

    def _split(self, text: str) -> List[tuple]:
        """
        Dispatch to the correct splitting strategy.

        Returns:
            List of (content, char_start, char_end) tuples.
        """
        strategy = self.config.strategy
        if strategy == ChunkStrategy.CHARACTER:
            return self._character_split(text)
        if strategy == ChunkStrategy.SENTENCE:
            return self._sentence_split(text)
        if strategy == ChunkStrategy.PARAGRAPH:
            return self._paragraph_split(text)
        if strategy == ChunkStrategy.RECURSIVE:
            return self._recursive_split(text)
        return self._character_split(text)

    # ------------------------------------------------------------------
    # CHARACTER strategy
    # ------------------------------------------------------------------

    def _character_split(self, text: str) -> List[tuple]:
        """Fixed-size character windows with optional word-boundary snapping."""
        size = self.config.chunk_size
        overlap = self.config.overlap
        step = max(1, size - overlap)
        results: List[tuple] = []
        start = 0

        while start < len(text):
            end = min(start + size, len(text))

            if self.config.respect_word_boundaries and end < len(text):
                # Walk back to the nearest space to avoid splitting a word
                snap = text.rfind(" ", start, end)
                if snap > start:
                    end = snap + 1  # include the space in the current chunk

            chunk = text[start:end]
            if self.config.strip_whitespace:
                chunk = chunk.strip()

            if len(chunk) >= self.config.min_chunk_size:
                results.append((chunk, start, end))

            if end >= len(text):
                break
            start += step

        return results

    # ------------------------------------------------------------------
    # SENTENCE strategy
    # ------------------------------------------------------------------

    def _sentence_split(self, text: str) -> List[tuple]:
        """Split on sentence boundaries, then window long sentences."""
        sentences = _SENTENCE_SPLIT.split(text)
        return self._window_segments(sentences, text)

    # ------------------------------------------------------------------
    # PARAGRAPH strategy
    # ------------------------------------------------------------------

    def _paragraph_split(self, text: str) -> List[tuple]:
        """Split on blank lines, then window long paragraphs."""
        paragraphs = _PARA_SPLIT.split(text)
        return self._window_segments(paragraphs, text)

    # ------------------------------------------------------------------
    # RECURSIVE strategy
    # ------------------------------------------------------------------

    def _recursive_split(self, text: str) -> List[tuple]:
        """
        Multi-level recursive split: paragraph → sentence → character.

        First split by paragraphs.  If a paragraph is still larger than
        chunk_size, split it by sentences.  If sentences are still too
        large, fall back to the character splitter.
        """
        size = self.config.chunk_size
        paragraphs = _PARA_SPLIT.split(text)
        segments: List[str] = []

        for para in paragraphs:
            if not para.strip():
                continue
            if len(para) <= size:
                segments.append(para)
            else:
                sentences = _SENTENCE_SPLIT.split(para)
                for sent in sentences:
                    if not sent.strip():
                        continue
                    if len(sent) <= size:
                        segments.append(sent)
                    else:
                        # Final fallback: character-split the long sentence
                        sub = self._character_split(sent)
                        segments.extend(s[0] for s in sub)

        return self._window_segments(segments, text)

    # ------------------------------------------------------------------
    # Shared windowing helper
    # ------------------------------------------------------------------

    def _window_segments(self, segments: List[str], original: str) -> List[tuple]:
        """
        Merge short segments into windows of at most ``chunk_size`` characters,
        respecting ``overlap`` by including the tail of the previous window.

        Args:
            segments: Pre-split text segments (sentences, paragraphs, …).
            original: The original unsplit text (used to track char offsets).

        Returns:
            List of (content, char_start, char_end) tuples.
        """
        size = self.config.chunk_size
        results: List[tuple] = []
        current: List[str] = []
        current_len = 0
        # Track position in the original string
        search_from = 0

        def flush(parts: List[str]) -> None:
            content = " ".join(parts)
            if self.config.strip_whitespace:
                content = content.strip()
            if len(content) < self.config.min_chunk_size:
                return
            # Locate char_start in the original text
            start_idx = original.find(parts[0].strip(), search_from)
            if start_idx == -1:
                start_idx = 0
            end_idx = start_idx + len(content)
            results.append((content, start_idx, min(end_idx, len(original))))

        for seg in segments:
            seg = seg.strip() if self.config.strip_whitespace else seg
            if not seg:
                continue
            seg_len = len(seg)

            if current_len + seg_len + 1 > size and current:
                flush(current)
                # Keep overlap by retaining the last segment
                overlap_segs = current[-1:] if self.config.overlap > 0 else []
                current = overlap_segs
                current_len = sum(len(s) for s in current)

            current.append(seg)
            current_len += seg_len + 1  # +1 for the space separator

        if current:
            flush(current)

        return results
