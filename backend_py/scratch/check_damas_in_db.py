import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.tender import Tender

db = SessionLocal()
try:
    damas_ids = ["26120012489236", "26120012489237", "26120012489240"]
    for ext_id in damas_ids:
        t = db.query(Tender).filter(Tender.external_id == ext_id).first()
        if t:
            print(f"✅ Found in DB: ID: {t.id} | External ID: {t.external_id} | Title: {t.title} | Created At: {t.created_at}")
        else:
            print(f"❌ NOT found in DB: External ID {ext_id}")
finally:
    db.close()
