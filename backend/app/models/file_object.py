"""FileObject model for storage metadata."""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.document_version import DocumentVersion


class FileObject(Base, TimestampMixin):
    """Storage metadata for uploaded files.
    
    This separates storage concerns from document business logic,
    enabling multiple versions of documents to share storage references.
    """

    __tablename__ = "file_objects"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Storage details
    storage_provider: Mapped[str] = mapped_column(String(50), nullable=False)  # s3, uploadthing, local
    bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    
    # File metadata
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Relationships
    document_versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="file_object", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FileObject(id={self.id}, key='{self.object_key[:50]}...')>"
