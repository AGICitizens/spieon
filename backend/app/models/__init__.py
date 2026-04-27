"""SQLModel table definitions.

Importing this package registers every `table=True` model with SQLModel.metadata,
which is what Alembic autogenerate reads when producing migrations.
"""

from app.models.base import TimestampMixin, utcnow
from app.models.finding import Finding, Severity
from app.models.scan import Scan, ScanStatus

__all__ = [
    "Finding",
    "Scan",
    "ScanStatus",
    "Severity",
    "TimestampMixin",
    "utcnow",
]
