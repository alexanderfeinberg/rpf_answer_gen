from typing import Iterable

class Chunker:
    def __init__(self, model_name : str, chunk_chars : int = 500, overlap : int = 50):
        """Configure token-aware chunking behavior for extracted document pages."""
        self._model_name = model_name
        self._chunk_chars = chunk_chars
        self._overlap = overlap

    def __call__(self, pages : Iterable[str]) -> list[str]:
        """Yield per-page chunk lists as `(page_number, split_chunks)` pairs."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name = self._model_name,
            chunk_size = self._chunk_chars,
            chunk_overlap = self._overlap,
            separators = ['\n\n', '\n', ". ", "! ", "? ", " ", ""]
        )

        for page_number, page_text in pages:
            yield page_number, splitter.split_text(page_text)
