import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    print("Inspecting indexes to find unique title_hash constraint...")
    
    # 1. Look for unique indexes/constraints on tenders table for title_hash
    result = conn.execute(text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'tenders' AND indexdef LIKE '%title_hash%';
    """))
    
    indexes = result.fetchall()
    print(f"Found {len(indexes)} matching indexes:")
    for row in indexes:
        print(f"  Index: {row[0]}")
        print(f"  Def: {row[1]}")
        
    # Drop index if it is a unique index
    for row in indexes:
        idx_name = row[0]
        if "UNIQUE" in row[1]:
            print(f"Dropping unique index: {idx_name}...")
            try:
                conn.execute(text(f"DROP INDEX IF EXISTS {idx_name} CASCADE;"))
                conn.commit()
                print("Index dropped successfully.")
            except Exception as e:
                print(f"Failed to drop index {idx_name}: {e}")
                conn.rollback()

    # 2. Look for unique constraints on tenders table for title_hash
    result = conn.execute(text("""
        SELECT conname, pg_get_constraintdef(oid) 
        FROM pg_constraint 
        WHERE conrelid = 'tenders'::regclass AND pg_get_constraintdef(oid) LIKE '%title_hash%';
    """))
    
    constraints = result.fetchall()
    print(f"Found {len(constraints)} matching constraints:")
    for row in constraints:
        print(f"  Constraint: {row[0]}")
        print(f"  Def: {row[1]}")
        
    for row in constraints:
        con_name = row[0]
        print(f"Dropping unique constraint: {con_name}...")
        try:
            conn.execute(text(f"ALTER TABLE tenders DROP CONSTRAINT IF EXISTS {con_name} CASCADE;"))
            conn.commit()
            print("Constraint dropped successfully.")
        except Exception as e:
            print(f"Failed to drop constraint {con_name}: {e}")
            conn.rollback()

    # 3. Create a plain non-unique index on title_hash if none remains
    try:
        print("Creating plain index idx_tenders_title_hash on title_hash...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tenders_title_hash ON tenders(title_hash);"))
        conn.commit()
        print("Plain index created successfully.")
    except Exception as e:
        print(f"Failed to create plain index: {e}")
        conn.rollback()

    print("\nDatabase fix completed.")
