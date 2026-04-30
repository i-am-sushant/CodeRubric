"""
Code embedding module using local sentence-transformers.

Converts code chunks to vector embeddings for storage in ChromaDB.
Runs entirely locally — no API key required.
"""

import asyncio
import logging
from typing import List
from dataclasses import asdict

from sentence_transformers import SentenceTransformer

from .chunker import CodeChunk


logger = logging.getLogger(__name__)

_MODEL_CACHE: dict = {}


def _get_model(model_name: str) -> SentenceTransformer:
    """Load and cache a SentenceTransformer model."""
    if model_name not in _MODEL_CACHE:
        logger.info(f"Loading sentence-transformers model: {model_name}")
        _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
        logger.info(f"Model loaded: {model_name}")
    return _MODEL_CACHE[model_name]


class CodeEmbedder:
    """Creates embeddings for code chunks using a local sentence-transformers model."""

    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    DEFAULT_BATCH_SIZE = 64

    def __init__(
        self,
        api_key: str = None,  # kept for interface compatibility, unused
        model: str = None,
        batch_size: int = None,
    ):
        """
        Initialize the embedder.

        Args:
            api_key: Ignored (kept for API compatibility with OpenAI variant)
            model: Sentence-transformers model name (defaults to all-MiniLM-L6-v2)
            batch_size: Number of texts to encode per batch
        """
        self.model_name = model or self.DEFAULT_MODEL
        self.batch_size = batch_size or self.DEFAULT_BATCH_SIZE
        self._st_model = _get_model(self.model_name)
        logger.info(f"Initialized CodeEmbedder with local model: {self.model_name}")

    def _encode(self, texts: List[str]) -> List[List[float]]:
        """Encode texts synchronously in batches."""
        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            vectors = self._st_model.encode(batch, show_progress_bar=False)
            all_embeddings.extend(v.tolist() for v in vectors)
            logger.debug(
                f"Encoded batch {i // self.batch_size + 1}/"
                f"{(len(texts) - 1) // self.batch_size + 1}"
            )
        return all_embeddings

    async def embed_chunks(self, chunks: List[CodeChunk]) -> List[dict]:
        """
        Embed multiple code chunks.

        Args:
            chunks: List of CodeChunk objects

        Returns:
            List of dicts with 'chunk', 'embedding', and 'id' keys
        """
        if not chunks:
            return []

        texts = [chunk.to_embedding_text() for chunk in chunks]
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(None, self._encode, texts)

        results = []
        for chunk, embedding in zip(chunks, embeddings):
            results.append({"chunk": asdict(chunk), "embedding": embedding, "id": chunk.id})

        logger.info(f"Embedded {len(chunks)} chunks")
        return results

    async def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, self._encode, [text])
        return results[0]

    async def embed_query(self, query: str) -> List[float]:
        """
        Embed a search query.

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        return await self.embed_text(query)

    def embed_chunks_sync(self, chunks: List[CodeChunk]) -> List[dict]:
        """Synchronous wrapper for embed_chunks."""
        return asyncio.run(self.embed_chunks(chunks))

    def embed_text_sync(self, text: str) -> List[float]:
        """Synchronous wrapper for embed_text."""
        return asyncio.run(self.embed_text(text))
