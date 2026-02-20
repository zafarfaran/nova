"""Tax-specific SQLAlchemy models adapted from Helio for Nova's PostgreSQL database.

These models extend Nova's schema with tax planning and advisory tables.
All models use Nova's Base + TimestampMixin and reference Nova's clients.id
as an Integer foreign key.
"""

from app.models.tax.context_snippet import TaxContextSnippet
from app.models.tax.conversation import TaxConversation
from app.models.tax.meeting_note import TaxMeetingNote
from app.models.tax.message import TaxMessage
from app.models.tax.observation import TaxObservation
from app.models.tax.tax_profile import TaxProfile

__all__ = [
    "TaxProfile",
    "TaxObservation",
    "TaxMeetingNote",
    "TaxConversation",
    "TaxMessage",
    "TaxContextSnippet",
]
