"""Database Management for OrderPilot-AI Trading Application.

Handles database initialization, session management, and common operations.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.config.loader import DatabaseConfig

from .models import AITelemetry, Alert, Base, MarketBar

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, config: DatabaseConfig):
        """Initialize the database manager.

        Args:
            config: Database configuration
        """
        self.config = config
        self.engine: Engine | None = None
        self.session_factory: sessionmaker | None = None
        self.scoped_session: scoped_session | None = None

    def initialize(self) -> None:
        """Initialize the database connection and create tables."""
        # Create database directory if needed
        if self.config.engine == "sqlite":
            db_path = Path(self.config.path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            connection_string = f"sqlite:///{db_path}"

            # SQLite specific configuration
            self.engine = create_engine(
                connection_string,
                connect_args={
                    "check_same_thread": False,
                    "timeout": self.config.pool_timeout_seconds
                },
                poolclass=StaticPool,
                echo=False
            )

            # Enable foreign keys for SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, _connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                if self.config.auto_vacuum:
                    cursor.execute("PRAGMA auto_vacuum=FULL")
                cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
                cursor.close()

        elif self.config.engine == "postgresql":
            # PostgreSQL connection (for TimescaleDB)
            connection_string = (
                f"postgresql://{self.config.username}:{self.config.password}@"
                f"{self.config.host}:{self.config.port}/{self.config.database}"
            )
            self.engine = create_engine(
                connection_string,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout_seconds,
                echo=False
            )
        else:
            raise ValueError(f"Unsupported database engine: {self.config.engine}")

        # Create session factory
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.scoped_session = scoped_session(self.session_factory)

        # Create all tables
        self.create_tables()

        logger.info(f"Database initialized: {self.config.engine} at {self.config.path}")

    def create_tables(self) -> None:
        """Create all database tables."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")

        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")

        # Create indexes for TimescaleDB if applicable
        if self.config.engine == "postgresql":
            self._create_timescale_hypertables()

    def _create_timescale_hypertables(self) -> None:
        """Create TimescaleDB hypertables for time-series data."""
        with self.engine.connect() as conn:
            try:
                # Create TimescaleDB extension
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))

                # Convert tables to hypertables
                tables_to_convert = [
                    ("market_bars", "timestamp"),
                    ("ai_telemetry", "requested_at"),
                    ("audit_log", "occurred_at"),
                    ("system_metrics", "recorded_at")
                ]

                for table_name, time_column in tables_to_convert:
                    try:
                        conn.execute(text(
                            f"SELECT create_hypertable('{table_name}', '{time_column}', "
                            f"if_not_exists => TRUE);"
                        ))
                        logger.info(f"Created hypertable for {table_name}")
                    except Exception as e:
                        logger.warning(f"Could not create hypertable for {table_name}: {e}")

                conn.commit()
            except Exception as e:
                logger.warning(f"TimescaleDB setup skipped: {e}")

    def drop_tables(self) -> None:
        """Drop all database tables. USE WITH CAUTION!"""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")

        Base.metadata.drop_all(self.engine)
        logger.warning("All database tables dropped")

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provide a transactional scope for database operations.

        Yields:
            Database session

        Example:
            with db_manager.session() as session:
                session.add(order)
                session.commit()
        """
        if not self.scoped_session:
            raise RuntimeError("Database not initialized")

        session = self.scoped_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """Get a new database session.

        Returns:
            Database session

        Note:
            Caller is responsible for closing the session.
        """
        if not self.session_factory:
            raise RuntimeError("Database not initialized")

        return self.session_factory()

    def execute_raw(self, query: str, params: dict | None = None) -> Any:
        """Execute a raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query result
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            return result

    def backup(self, backup_path: Path) -> None:
        """Create a database backup (SQLite only).

        Args:
            backup_path: Path to save the backup
        """
        if self.config.engine != "sqlite":
            logger.warning("Backup only supported for SQLite databases")
            return

        import shutil

        # For SQLite, we can just copy the file
        source_path = Path(self.config.path)
        if source_path.exists():
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
        else:
            logger.error(f"Source database not found: {source_path}")

    def vacuum(self) -> None:
        """Perform database maintenance (VACUUM for SQLite)."""
        if self.config.engine == "sqlite":
            with self.engine.connect() as conn:
                conn.execute(text("VACUUM;"))
                logger.info("Database vacuumed")
        else:
            logger.info("Vacuum not needed for this database engine")

    def get_table_stats(self) -> dict:
        """Get statistics about database tables.

        Returns:
            Dictionary with table names and row counts
        """
        stats = {}
        with self.session() as session:
            for table in Base.metadata.tables.keys():
                count_query = text(f"SELECT COUNT(*) FROM {table}")
                result = session.execute(count_query)
                stats[table] = result.scalar()

        return stats

    def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Clean up old data from the database.

        Args:
            days_to_keep: Number of days of data to keep
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        with self.session() as session:
            # Clean up old market bars
            deleted = session.query(MarketBar).filter(
                MarketBar.timestamp < cutoff_date
            ).delete()
            logger.info(f"Deleted {deleted} old market bars")

            # Clean up old AI telemetry
            deleted = session.query(AITelemetry).filter(
                AITelemetry.requested_at < cutoff_date
            ).delete()
            logger.info(f"Deleted {deleted} old AI telemetry records")

            # Clean up acknowledged alerts
            deleted = session.query(Alert).filter(
                Alert.acknowledged_at < cutoff_date,
                Alert.is_acknowledged == True
            ).delete()
            logger.info(f"Deleted {deleted} old acknowledged alerts")

            session.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self.scoped_session:
            self.scoped_session.remove()
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# Global database manager instance
db_manager: DatabaseManager | None = None


def initialize_database(config: DatabaseConfig) -> DatabaseManager:
    """Initialize the global database manager.

    Args:
        config: Database configuration

    Returns:
        Initialized database manager
    """
    global db_manager
    db_manager = DatabaseManager(config)
    db_manager.initialize()
    return db_manager


def get_db_manager() -> DatabaseManager:
    """Get the global database manager.

    Returns:
        Database manager instance

    Raises:
        RuntimeError: If database not initialized
    """
    if not db_manager:
        raise RuntimeError("Database not initialized. Call initialize_database first.")
    return db_manager