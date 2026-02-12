from __future__ import annotations

import logging
from typing import Iterable, Sequence, Tuple, Any, List
from answer_gen.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str | None = None,
        batch_size: int = 32,
        normalize: bool = True,
    ) -> None:
        # Soft dependency: only import heavy ML deps when the embedder is constructed.
        import torch  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore

        # Resolve device early to avoid surprising CPU fallback mid-flight.
        resolved_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = SentenceTransformer(model_name, device=resolved_device)
        self._batch_size = batch_size
        self._normalize = normalize
        self._device = resolved_device
        self._torch = torch
        logger.info("Embedder initialized with model=%s device=%s", model_name, resolved_device)

    def encode(self, texts: Sequence[str]) -> List[List[float]]:
        torch = self._torch
        if not texts:
            return []
        with torch.inference_mode():
            try:
                embeddings = self._model.encode(
                    list(texts),
                    batch_size=self._batch_size,
                    convert_to_numpy=True,
                    normalize_embeddings=self._normalize,
                    show_progress_bar=False,
                )
            except Exception as e:
                raise EmbeddingError('An error occured while embedding text.')

        return embeddings.tolist()

    def encode_with_ids(self, items: Iterable[Tuple[Any, str]]) -> List[Tuple[Any, List[float]]]:
        ids: List[Any] = []
        texts: List[str] = []
        for item_id, text in items:
            ids.append(item_id)
            texts.append(text)
        vectors = self.encode(texts)
        return list(zip(ids, vectors))

    def __call__(self, texts: Sequence[str]) -> List[List[float]]:
        return self.encode(texts)
