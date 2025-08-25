"""
Database initialization script for Media Monitoring Agent
"""
import sys
from database import init_database, check_database_connection, engine
from sqlalchemy import text

def create_indexes():
    """Create additional indexes for better performance"""
    try:
        with engine.connect() as conn:
            # Index on timestamp for pending_articles
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_pending_articles_timestamp 
                ON pending_articles(timestamp DESC)
            """))
            
            # Index on processed_date for processed_archive
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_processed_archive_processed_date 
                ON processed_archive(processed_date DESC)
            """))
            
            # Index on category for hansard_questions
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_hansard_questions_category 
                ON hansard_questions(category)
            """))
            
            conn.commit()
            print("Database indexes created successfully")
            return True
    except Exception as e:
        print(f"Error creating indexes: {e}")
        return False

def verify_constraints():
    """Verify database constraints are working"""
    try:
        from database import SessionLocal, PendingArticle
        
        db = SessionLocal()
        
        # Test unique constraint on URL
        test_article1 = PendingArticle(
            url="https://test-duplicate.com",
            submitted_by="Test User"
        )
        db.add(test_article1)
        db.commit()
        
        # Try to add duplicate - should fail
        test_article2 = PendingArticle(
            url="https://test-duplicate.com",
            submitted_by="Another User"
        )
        db.add(test_article2)
        
        try:
            db.commit()
            print("ERROR: Duplicate URL constraint not working!")
            return False
        except Exception:
            db.rollback()
            print("✓ URL uniqueness constraint working correctly")
        
        # Clean up test data
        db.query(PendingArticle).filter(
            PendingArticle.url == "https://test-duplicate.com"
        ).delete()
        db.commit()
        db.close()
        
        return True
        
    except Exception as e:
        print(f"Error verifying constraints: {e}")
        return False

def main():
    """Main initialization function"""
    print("Initializing Media Monitoring Agent database...")
    
    # Check database connection
    if not check_database_connection():
        print("❌ Database connection failed")
        sys.exit(1)
    
    # Create tables
    if not init_database():
        print("❌ Database table creation failed")
        sys.exit(1)
    
    # Create indexes
    if not create_indexes():
        print("❌ Database index creation failed")
        sys.exit(1)
    
    # Verify constraints
    if not verify_constraints():
        print("❌ Database constraint verification failed")
        sys.exit(1)
    
    print("✅ Database initialization completed successfully")

if __name__ == "__main__":
    main()