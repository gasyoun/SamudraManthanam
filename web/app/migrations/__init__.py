"""Ordered, checksum-tracked schema migrations (H1927 / Lane D1).

Two databases with deliberately different policies:

* ``state.db`` — mutable, long-lived, holds user/consent/correction/AI-cache
  rows that cannot be regenerated. It gets ordered SQL migrations applied by
  :mod:`app.migrations.runner`, each recorded with an immutable checksum.
* ``corpus.db`` — generated. It is never migrated in place; a schema change is
  a *rebuild requirement*. See :mod:`app.migrations.corpus_policy`.
"""

from app.migrations.runner import (
    MigrationError,
    MigrationChecksumError,
    MigrationMissingError,
    apply_migrations,
    apply_migrations_at_path,
    apply_migrations_sync,
    discover_migrations,
    state_migrations_dir,
)

__all__ = [
    "MigrationError",
    "MigrationChecksumError",
    "MigrationMissingError",
    "apply_migrations",
    "apply_migrations_at_path",
    "apply_migrations_sync",
    "discover_migrations",
    "state_migrations_dir",
]
