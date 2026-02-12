from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Tuple, List

from answer_gen.components.ingestion.chunker import Chunker
from answer_gen.utils.embedder import Embedder

from answer_gen.storage import Document, Chunk, ChunkVersion
from answer_gen.storage.persistence import Persistence
from answer_gen.storage.factories import document_factory, chunk_factory

from answer_gen.storage.db import build_bulk_connection
from answer_gen.utils.document_utils import get_document_hash, get_document_text

import answer_gen.exceptions as exceptions


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DocumentIngestorConfig:
    max_insert_chunks: int
    chunk_window: int
    chunk_overlap: int
    chunk_token_model_name: str
    chunk_version_name: str
    embed_buffer_size: int | None = None


class DocumentIngestorWorker:
    """Orchestrates deduplication, chunking, embedding, and bulk insert for documents."""

    def __init__(
        self,
        db_url: str,
        config: DocumentIngestorConfig,
    ):
        """Configure the ingestor with DB connection info, chunking, and embedding settings."""
        self._db_url = db_url
        self._config = config

        self._chunker = Chunker(
            model_name=config.chunk_token_model_name,
            chunk_chars=config.chunk_window,
            overlap=config.chunk_overlap,
        )

        self._embedder = Embedder()

    async def __call__(self, documents: Iterable[Tuple[str, bytes]]) -> List[tuple]:
        """Ingest a batch of (filename, bytes) documents and return inserted document IDs.
        """
        documents = list(documents)
        inserted_ids: List[int] = []
        failed_docs: dict[str, str] = {}
        logger.info("Starting document ingestion documents=%s", len(documents))

        with build_bulk_connection(self._db_url) as session:
            # Keep a single DB transaction/session for the ingestion batch.
            persistence = Persistence(session)
            effective_chunk_version: ChunkVersion | None = (
                persistence.get_chunk_version(self._config.chunk_version_name) if self._config.chunk_version_name else None
            )
            logger.info(
                "Resolved chunk version requested=%s found=%s",
                self._config.chunk_version_name,
                effective_chunk_version.id if effective_chunk_version is not None else None,
            )

            # Validate requested chunk version exists (if provided)
            if effective_chunk_version is None:
                raise exceptions.InvalidResourceIdentifier(f"Chunk version {self._config.chunk_version_name} does not exist.")

            to_insert = self._dedupe_documents(documents, persistence)
            logger.info("Deduplicated documents incoming=%s to_insert=%s", len(documents), len(to_insert))

            insert_batch: List[Chunk] = []

            for filename, doc_content, doc_hash in to_insert:
                doc_insert_batch: List[Chunk] = []

                # Each document is inserted first so chunks can reference document ID.
                document: Document | None = None
                logger.info("Processing document filename=%s", filename)
                try:
                    document = self._insert_document(persistence, filename, filename, doc_hash)
                    self._build_document_chunks(document, effective_chunk_version, doc_content, doc_insert_batch)

                    # Merge only fully successful document chunks into the shared batch.
                    if doc_insert_batch:
                        insert_batch.extend(doc_insert_batch)
                        if len(insert_batch) >= self._config.max_insert_chunks:
                            self._bulk_insert_chunks(persistence, insert_batch[: self._config.max_insert_chunks])
                            del insert_batch[: self._config.max_insert_chunks]
                except exceptions.StorageWriteError as e:
                    logger.warning("Document insert failed filename=%s error=%s", filename, str(e))
                    failed_docs[filename] = str(e)
                    continue
                except Exception as e:
                    if document is not None:
                        persistence.delete_document(document)
                    logger.exception("Document ingestion failed filename=%s", filename)
                    failed_docs[filename] = str(e)
                    continue

                inserted_ids.append(document.id)
                logger.info(
                    "Document ingestion staged filename=%s document_id=%s buffered_chunks=%s pending_chunks=%s",
                    filename,
                    document.id,
                    len(doc_insert_batch),
                    len(insert_batch),
                )

            if insert_batch:
                self._bulk_insert_chunks(persistence, insert_batch)
                insert_batch.clear()

            persistence.commit()
            logger.info("Committed document ingestion batch inserted=%s failed=%s", len(inserted_ids), len(failed_docs))

        if len(failed_docs) == len(documents):
            fails = str(len(failed_docs))
            logger.warning("All document uploads failed total=%s", fails)
            raise exceptions.BulkUploadFailed(f'Failed to upload all {fails} documents. Could you please retry with other documents?')

        logger.info(
            "Completed document ingestion inserted=%s failed=%s",
            len(inserted_ids),
            len(failed_docs),
        )
        return inserted_ids, failed_docs

    def _build_document_chunks(self, document : Document,
                               chunk_version : ChunkVersion, doc_content, insert_batch : list):
        """Build chunks for one document and flush buffered embeddings/inserts in batches."""
        embed_buffer: List[Chunk] = []
        embed_buffer_size = self._config.embed_buffer_size or 512
        chunk_count = 0
        for chunk in self._build_chunks(document.id, doc_content, chunk_version.id):
            # Buffer chunks so embeddings and inserts can be batched.
            embed_buffer.append(chunk)
            chunk_count += 1

            if len(embed_buffer) >= embed_buffer_size:
                self._handle_buffer_flush(embed_buffer, insert_batch)

        if embed_buffer:
            self._handle_buffer_flush(embed_buffer, insert_batch)

        logger.info(
            "Built chunks for document document_id=%s chunk_count=%s",
            document.id,
            chunk_count,
        )

    def _handle_buffer_flush(self, embed_buffer : list, insert_batch : list):
        """Embed buffered chunks and move them into the pending insert batch."""
        logger.debug(
            "Flushing embed buffer size=%s pending_insert_batch=%s",
            len(embed_buffer),
            len(insert_batch),
        )
        self._attach_embeddings(embed_buffer)
        insert_batch.extend(embed_buffer)
        embed_buffer.clear()

    def _dedupe_documents(self, documents: Iterable[Tuple[str, bytes]], persistence: Persistence) -> Iterable[Tuple[str, bytes, str]]:
        """Remove already-ingested docs by comparing content hashes against the database."""
        docs = list(documents)
        doc_names = [d_name for d_name, _ in docs]
        doc_contents = [d_content for _, d_content in docs]
        doc_hashes = [get_document_hash(content) for content in doc_contents]

        doc_info = zip(doc_names, doc_contents, doc_hashes)
        existing_hashes = {doc.hash for doc in persistence.get_documents_by_hashes(doc_hashes)}

        return [
            (doc_name, doc_content, doc_hash)
            for doc_name, doc_content, doc_hash in doc_info
            if doc_hash not in existing_hashes
        ]

    def _insert_document(self, persistence: Persistence, filename, storage_url, doc_hash) -> Document:
        """Create and persist a Document row, returning the instance with its ID populated."""
        document : Document = document_factory(
            filename, storage_url, doc_hash
        )
        persistence.insert_document(document)
        persistence.flush() # get document.id for FK usage
        logger.debug("Inserted document row filename=%s document_id=%s", filename, document.id)

        return document

    def _build_chunks(self, document_id: int, doc_bytes: bytes, chunk_version_id: int) -> Iterable[Chunk]:
        """Chunk a document's text into Chunk ORM objects, preserving order and chunk version."""
        try:
            # Source of truth for PDF text extraction by page.
            pages = get_document_text(doc_bytes)
        except Exception as e:
            logger.exception(f'An error occured while extracting document text.')
            raise

        order_counter = 0
        for _, split_chunks in self._chunker(pages):
            for chunk_text in split_chunks:
                # Persist deterministic chunk ordering for retrieval and debugging.
                yield chunk_factory(
                    doc_id=document_id,
                    order=order_counter,
                    content=chunk_text,
                    chunk_version_id=chunk_version_id,
                )
                order_counter += 1

    def _attach_embeddings(self, chunks: List[Chunk]) -> None:
        """Compute embeddings for chunk.content and attach to chunk.embedding."""
        if not chunks:
            return
        texts = [c.content for c in chunks]
        logger.debug("Encoding embeddings for chunk batch size=%s", len(texts))

        try:
            vectors = self._embedder.encode(texts)
        except Exception:
            logger.exception('An error occured when creating embeddings.')
            raise

        if len(vectors) != len(chunks):
            vec_count = str(len(vectors))
            chnk_count = str(len(chunks))

            logger.exception(f'Embedding count does not match chunk count. Got {vec_count} embeddings and {chnk_count} chunks.')
            raise RuntimeError("Embedding count mismatch for chunks batch")

        for chunk, vector in zip(chunks, vectors):
            chunk.embedding = vector

    def _bulk_insert_chunks(self, persistence: Persistence, chunks: List[Chunk]) -> None:
        """Bulk insert a list of Chunk objects using the provided repo."""
        if not chunks:
            return

        persistence.bulk_insert_chunks(chunks)
        logger.debug("Bulk inserted chunks count=%s", len(chunks))
