"""DB session/engine come from shared libs.

This module exists so the auth service can import DB concerns from a single place
(and keep api/application layers free of direct libs.* imports if desired).
"""

from libs.db.postgres import engine, get_db

__all__ = ["engine", "get_db"]
