import abc
import hashlib
from typing import List
from openai import OpenAI
from app.core.config import settings


class BaseEmbeddings(abc.ABC):
    """Abstract Base Class for Embedding generation, supporting dependency inversion."""

    @abc.abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents."""
        pass

    @abc.abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single search query."""
        pass


class OpenAIEmbeddings(BaseEmbeddings):
    """OpenAI API client wrapper for generating text embeddings (e.g. text-embedding-3-small)."""

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        # Initialized lazily to prevent boot failures if key is missing during build time
        self._client = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=settings.GROQ_API_KEY)  # or OPENAI_API_KEY if defined
        return self._client

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(input=texts, model=self.model)
            return [data.embedding for data in response.data]
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding failure: {e}") from e

    def embed_query(self, text: str) -> List[float]:
        embeddings = self.embed_documents([text])
        return embeddings[0]


class LocalEmbeddings(BaseEmbeddings):
    """
    Lightweight, build-safe local embedding generator.
    Produces deterministic float vectors of size 1536.
    Does NOT import PyTorch or SentenceTransformers, keeping builds fast,
    memory-efficient, and suitable for free-tier hosting (e.g. Render).
    """

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def _get_embedding(self, text: str) -> List[float]:
        # Perform a deterministic hash-frequency projection
        vec = [0.0] * self.dimension
        if not text:
            return vec
            
        # Clean text and extract byte chunks
        cleaned = text.lower().strip()
        words = cleaned.split()
        
        # Accumulate hash positions
        for word in words:
            # Hash word to find position
            h = hashlib.sha256(word.encode("utf-8")).hexdigest()
            pos = int(h, 16) % self.dimension
            vec[pos] += 1.0
            
        # Normalize vector
        total = sum(v * v for v in vec) ** 0.5
        if total > 0:
            vec = [v / total for v in vec]
            
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._get_embedding(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._get_embedding(text)
