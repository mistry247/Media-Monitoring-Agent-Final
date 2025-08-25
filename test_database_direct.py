#!/usr/bin/env python3
"""
Direct database test - bypassing the web server completely
"""
import sqlite3
import os
from datetime import datetime

def test_database_direct():
    """Test database operations directly"""
    print("🔍 Testing direct database access...")
    
    # Check if database file exists
    db_path = "media_monitoring.db"
    print(f"Database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    try:
        # Connect to SQLite database
        print("📡 Connecting to database...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if pending_articles table exists
        print("🔍 Checking if pending_articles table exists...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pending_articles';")
        table_exists = cursor.fetchone()
        print(f"Table exists: {table_exists is not None}")
        
        if not table_exists:
            print("📝 Creating pending_articles table...")
            cursor.execute("""
                CREATE TABLE pending_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    submitted_by TEXT NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            """)
            conn.commit()
            print("✅ Table created successfully")
        
        # Insert a test record
        print("📝 Inserting test record...")
        test_url = "https://example.com/direct-test"
        test_submitter = "Direct Test User"
        test_timestamp = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO pending_articles (url, submitted_by, timestamp)
            VALUES (?, ?, ?)
        """, (test_url, test_submitter, test_timestamp))
        
        conn.commit()
        
        # Get the inserted record ID
        record_id = cursor.lastrowid
        print(f"✅ Record inserted with ID: {record_id}")
        
        # Query the record back
        print("🔍 Querying record back...")
        cursor.execute("SELECT * FROM pending_articles WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        print(f"✅ Retrieved record: {record}")
        
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM pending_articles")
        count = cursor.fetchone()[0]
        print(f"📊 Total records in table: {count}")
        
        conn.close()
        print("✅ Database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_direct()
    if success:
        print("\n🎉 Database is working correctly!")
    else:
        print("\n💥 Database has issues!")