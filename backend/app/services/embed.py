"""Text -> 384 numbers.

Uses fastembed (ONNX) rather than sentence-transformers, so no machine on the
team needs PyTorch: ~150MB instead of ~2.5GB. Model files download on first use
and are cached by fastembed after that.

The query/document distinction matters. BGE models are trained with an
instruction prefix on QUERIES and none on documents. Measured on our corpus,
applying it widens the gap between a covered question and an off-topic one from
+0.012 to +0.050 - four times the separation for one string concatenation.
Prefixing stored documents as well would undo the benefit.

Vectors come back unit-normalised, so cosine similarity equals the dot product.
"""

from __future__ import annotations

from functools import lru_cache

from .. import config

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _model():
    # Imported lazily so `import app.main` (and therefore the test suite) does
    # not pay the model load, and does not need the model present at all.
    from fastembed import TextEmbedding

    return TextEmbedding(config.EMBEDDING_MODEL)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed stored passages. No prefix."""
    return [list(map(float, v)) for v in _model().embed(texts)]


def embed_document(text: str) -> list[float]:
    return embed_documents([text])[0]


def embed_query(question: str) -> list[float]:
    """Embed a question. Prefixed - see the module docstring."""
    return embed_documents([QUERY_PREFIX + question])[0]
