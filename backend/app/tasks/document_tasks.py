"""Backward compatibility: Re-export from new location."""

from app.tasks.documents import (
    process_document,
    run_process_document,
    reprocess_failed_documents,
)

__all__ = [
    "process_document",
    "run_process_document",
    "reprocess_failed_documents",
]
