import os
import sys

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.tender import Tender
from sqlalchemy import func

db = SessionLocal()
try:
    # Group by title_hash and see how many duplicate titles exist in the DB (or would be blocked if they were new)
    # But wait, since we have a unique/exact match constraint on title_hash in is_duplicate,
    # there should be NO duplicate title_hashes in the DB at all!
    # Let's verify if all title_hashes in the DB are unique.
    title_counts = db.query(Tender.title_hash, func.count(Tender.id)).group_by(Tender.title_hash).all()
    duplicate_titles = [tc for tc in title_counts if tc[1] > 1]
    print(f"Number of duplicate title_hashes in DB: {len(duplicate_titles)}")
    
    # Let's check some titles that are very common in uzbek tenders
    print("\nTotal tenders in database:")
    total = db.query(Tender).count()
    print(f"Total: {total}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
