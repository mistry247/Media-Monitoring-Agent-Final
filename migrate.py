#!/usr/bin/env python3
"""
Database migration script for Media Monitoring Agent

This script handles database schema migrations for production deployments.
It tracks applied migrations and ensures they are run in the correct order.
"""

import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import settings


class MigrationManager:
    """Manages database migrations for the Media Monitoring Agent."""
    
    def __init__(self, database_url: str):
        """Initialize the migration manager with database URL."""
        # Extract the database path from SQLite URL
        if database_url.startswith('sqlite:///'):
            self.db_path = database_url[10:]  # Remove 'sqlite:///'
        else:
            raise ValueError("Only SQLite databases are supported for migrations")
        
        self.migrations_dir = project_root / "migrations"
        self.ensure_migrations_table()
    
    def ensure_migrations_table(self):
        """Create the migrations tracking table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT UNIQUE NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT migration_name FROM schema_migrations ORDER BY migration_name"
            )
            return [row[0] for row in cursor.fetchall()]
    
    def get_pending_migrations(self) -> List[Tuple[str, Path]]:
        """Get list of migrations that need to be applied."""
        if not self.migrations_dir.exists():
            print(f"Migrations directory {self.migrations_dir} does not exist")
            return []
        
        applied = set(self.get_applied_migrations())
        pending = []
        
        # Get all .sql files in migrations directory
        for migration_file in sorted(self.migrations_dir.glob("*.sql")):
            migration_name = migration_file.stem
            if migration_name not in applied:
                pending.append((migration_name, migration_file))
        
        return pending
    
    def apply_migration(self, migration_name: str, migration_file: Path) -> bool:
        """Apply a single migration file."""
        try:
            print(f"Applying migration: {migration_name}")
            
            # Read the migration SQL
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Apply the migration
            with sqlite3.connect(self.db_path) as conn:
                # Execute the migration SQL
                conn.executescript(migration_sql)
                
                # Record that this migration was applied
                conn.execute(
                    "INSERT INTO schema_migrations (migration_name) VALUES (?)",
                    (migration_name,)
                )
                conn.commit()
            
            print(f"✓ Successfully applied migration: {migration_name}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to apply migration {migration_name}: {e}")
            return False
    
    def migrate(self) -> bool:
        """Apply all pending migrations."""
        pending = self.get_pending_migrations()
        
        if not pending:
            print("No pending migrations found. Database is up to date.")
            return True
        
        print(f"Found {len(pending)} pending migrations:")
        for migration_name, _ in pending:
            print(f"  - {migration_name}")
        
        print("\nApplying migrations...")
        
        success_count = 0
        for migration_name, migration_file in pending:
            if self.apply_migration(migration_name, migration_file):
                success_count += 1
            else:
                print(f"Migration failed. Stopping at {migration_name}")
                break
        
        if success_count == len(pending):
            print(f"\n✓ All {success_count} migrations applied successfully!")
            return True
        else:
            print(f"\n✗ Applied {success_count}/{len(pending)} migrations")
            return False
    
    def status(self):
        """Show migration status."""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        print("Migration Status:")
        print(f"Database: {self.db_path}")
        print(f"Applied migrations: {len(applied)}")
        print(f"Pending migrations: {len(pending)}")
        
        if applied:
            print("\nApplied migrations:")
            for migration in applied:
                print(f"  ✓ {migration}")
        
        if pending:
            print("\nPending migrations:")
            for migration_name, _ in pending:
                print(f"  - {migration_name}")
        
        if not pending:
            print("\n✓ Database is up to date!")


def main():
    """Main migration script entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument(
        "command",
        choices=["migrate", "status"],
        help="Command to run"
    )
    parser.add_argument(
        "--database-url",
        help="Database URL (defaults to config value)"
    )
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or settings.DATABASE_URL
    
    try:
        manager = MigrationManager(database_url)
        
        if args.command == "migrate":
            success = manager.migrate()
            sys.exit(0 if success else 1)
        elif args.command == "status":
            manager.status()
            sys.exit(0)
            
    except Exception as e:
        print(f"Migration error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()