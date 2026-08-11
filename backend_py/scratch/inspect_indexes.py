import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    print("Listing all indexes on 'tenders' table:")
    result = conn.execute(text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'tenders';
    """))
    for row in result:
        print(f"Index: {row[0]}")
        print(f"Def: {row[1]}")
        print("-" * 50)
        
    print("\nListing constraints on 'tenders' table:")
    result = conn.execute(text("""
        SELECT conname, pg_get_constraintdef(oid) 
        FROM pg_constraint 
        WHERE conrelid = 'tenders'::regclass;
    """))
    for row in result:
        print(f"Constraint: {row[0]}")
        print(f"Def: {row[1]}")
        print("-" * 50)
