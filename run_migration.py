#!/usr/bin/env python3
"""
Run database migration to add has_content field to manual_input_articles table
"""

import sqlite3
import os
from pathlib import Path

def run_migration():
    """Run the database migration"""
    
    # Find the database file
    db_paths = [
        "data/media_monitoring.db",
        "media_monitoring.db"
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Database file not found!")
        print("Looked for:")
        for path in db_paths:
            print(f"  - {path}")
        return False
    
    print(f"📁 Found database at: {db_path}")
    
    # Read the migration file
    migration_file = "migrations/003_add_has_content_field.sql"
    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    print(f"📄 Read migration from: {migration_file}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if has_content column already exists
        cursor.execute("PRAGMA table_info(manual_input_articles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'has_content' in columns:
            print("✅ has_content column already exists, skipping migration")
            conn.close()
            return True
        
        print("🔄 Running migration...")
        
        # Split migration into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement:
                print(f"  Executing: {statement[:50]}...")
                cursor.execute(statement)
        
        # Commit changes
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(manual_input_articles)")
        columns_after = [column[1] for column in cursor.fetchall()]
        
        if 'has_content' in columns_after:
            print("✅ Migration completed successfully!")
            print("✅ has_content column added to manual_input_articles table")
            
            # Show sample data
            cursor.execute("SELECT id, url, has_content FROM manual_input_articles LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                print("\n📊 Sample data after migration:")
                for row in rows:
                    print(f"  ID {row[0]}: {row[1][:50]}... (has_content: {row[2]})")
        else:
            print("❌ Migration failed - has_content column not found after migration")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Running database migration...")
    success = run_migration()
    if success:
        print("\n🎉 Migration completed! You can now test the manual articles processing.")
    else:
        print("\n💥 Migration failed. Please check the errors above.")
