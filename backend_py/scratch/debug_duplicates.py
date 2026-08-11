import os
import sys

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.tender import Tender

db = SessionLocal()
try:
    total = db.query(Tender).count()
    print(f"Total tenders in DB: {total}")
    
    # Let's count by source
    from sqlalchemy import func
    counts = db.query(Tender.source, func.count(Tender.id)).group_by(Tender.source).all()
    print("Counts by source:")
    for source, cnt in counts:
        print(f"  {source}: {cnt}")
        
    # Let's see some etender/uzex items
    print("\nRecent UZEX/ETENDER tenders in DB:")
    recent = db.query(Tender).order_by(Tender.id.desc()).limit(20).all()
    for r in recent:
        title_repr = repr(r.title[:50])
        msg = f"ID: {r.id}, Source: {r.source}, ExtID: {r.external_id}, Title: {title_repr}, URL: {r.url}, title_hash: {r.title_hash}"
        print(msg.encode('ascii', errors='backslashreplace').decode('ascii'))
        
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
