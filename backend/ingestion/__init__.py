"""Local-first knowledge ingestion pipeline."""

from backend.ingestion.local_ingestion import (
    IngestionResult,
    LocalKnowledgeIngestionService,
)

__all__ = ["IngestionResult", "LocalKnowledgeIngestionService"]
