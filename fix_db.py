import sqlite3

# Connect to database
conn = sqlite3.connect('data/media_monitoring.db')
cursor = conn.cursor()

# Check if has_content column exists
cursor.execute("PRAGMA table_info(manual_input_articles)")
columns = [column[1] for column in cursor.fetchall()]

if 'has_content' not in columns:
    print("Adding has_content column...")
    cursor.execute("ALTER TABLE manual_input_articles ADD COLUMN has_content BOOLEAN DEFAULT 0")
    
    print("Updating existing records...")
    cursor.execute("UPDATE manual_input_articles SET has_content = CASE WHEN article_content IS NOT NULL AND TRIM(article_content) != '' THEN 1 ELSE 0 END")
    
    conn.commit()
    print("Migration completed successfully!")
else:
    print("has_content column already exists")

conn.close()
