from app.db.session import SessionLocal
from app.models.tender import Tender, TenderKeywordMatch, Keyword

def check_tenders_with_keywords() -> None:
    db = SessionLocal()
    try:
        # Найти тендеры с keyword matches
        tenders_with_matches = (
            db.query(Tender)
            .join(TenderKeywordMatch)
            .join(Keyword)
            .filter(Keyword.is_active == True)
            .limit(10)  # Последние 10
            .all()
        )

        print(f"Found {len(tenders_with_matches)} tenders with keyword matches:")
        for tender in tenders_with_matches:
            # Получить keywords для этого тендера
            matched_keywords = (
                db.query(Keyword)
                .join(TenderKeywordMatch)
                .filter(TenderKeywordMatch.tender_id == tender.id)
                .all()
            )
            
            keyword_phrases = ", ".join([kw.phrase for kw in matched_keywords])
            print(f"  - {tender.title[:50]}... (keywords: {keyword_phrases})")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_tenders_with_keywords()
