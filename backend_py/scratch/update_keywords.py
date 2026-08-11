import sys
import os

# Add parent directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.tender import Keyword, TenderKeywordMatch

def main():
    db = SessionLocal()
    try:
        # First clear out existing keyword matches since they depend on keywords
        print("Deleting existing tender keyword matches...")
        db.query(TenderKeywordMatch).delete()
        
        print("Deleting existing keywords...")
        db.query(Keyword).delete()
        db.commit()

        print("Existing keywords deleted.")

        new_keywords = [
            "теплица", "issiqxona", "ferma", "chorva", "parnik", "angar", "ombor",
            "sex", "metallokonstruktsiya", "metallokarkas", "sendvich panel", "armatura",
            "truba", "shveller", "dvutavr", "metall profil", "karkas", "qurilish",
            "stroyka", "rekonstruksiya", "modernizatsiya", "kapital remont", "ta'mirlash",
            "yangi obyekt", "genpodryad", "genpodryadchik", "issiqxona qurilishi",
            "qurilish materiallari", "stroy materialy", "стройматериалы", "ko'prik",
            "most", "tsex", "цех", "omborxona", "Yangi qurilish", "mukammal tamirlash",
            "мукаммал таъмирлаш", "таъмирлаш", "tamirlash", "реконструкция", "Rekonstruksiya",
            "иншоот қуриш", "янги умумтаълим мактаби қуриш", "комплекс янгидан қуриш",
            "янги МТТ қуриш", "янги бино қуриш", "мехмонхона қуриш", "кўприкни реконструкция қилиш",
            "завод қуриш"
        ]
        
        # Deduplicate, strip and lowercase to avoid case-sensitivity issues
        clean_keywords = list(set([k.strip().lower() for k in new_keywords if k.strip()]))
        
        print(f"Adding {len(clean_keywords)} new keywords...")

        for phrase in clean_keywords:
            kw = Keyword(phrase=phrase, is_active=True, is_blacklist=False)
            db.add(kw)
        
        db.commit()
        print("New keywords added successfully!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
