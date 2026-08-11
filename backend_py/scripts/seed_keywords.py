from app.db.session import SessionLocal
from app.models.tender import Keyword
from app.core.config import settings

def seed_keywords() -> None:
    print(f"Connecting to database: {settings.DATABASE_URL}")
    db = SessionLocal()

INITIAL_KEYWORDS = [
    # Основные keywordlar
    "теплица",
    "issiqxona",
    "ferma",
    "chorva",
    "parnik",
    "angar",
    "ombor",
    "sklad",
    "klaster",
    "zavod",
    "sex",
    # Metall keywordlar
    "metallokonstruktsiya",
    "metallokarkas",
    "sendvich panel",
    "armatura",
    "profnastil",
    "truba",
    "shveller",
    "dvutavr",
    "metall profil",
    "karkas",
    # Qurilish keywordlar
    "qurilish",
    "stroyka",
    "rekonstruksiya",
    "modernizatsiya",
    "kapital remont",
    "ta'mirlash",
    "yangi obyekt",
    "genpodryad",
    "genpodryadchik",
    "loyiha ishlari",
    "smeta",
    "PSD",
    # Agro keywordlar
    "agroklaster",
    "issiqxona qurilishi",
    "tomchilatib sug'orish",
    "chorva kompleksi",
    "parrandachilik",
    "suv xo'jaligi",
    "logistika markazi",
    "meva-sabzavot ombori",
    
    # NEW: Additional Uzbek/Russian terms for better coverage
    # Tender/procurement terms
    "tender",
    "konkurs",
    "zakupka",
    "postavka",
    "tender",
    "konkurs",
    "закупка",
    "поставка",
    "тендер",
    "конкурс",
    
    # Construction terms
    "montaj",
    "montazh",
    "loyiha",
    "proekt",
    "qurilish materiallari",
    "stroy materialy",
    "oborudovanie",
    "uskunalar",
    "remont",
    " servis",
    "service",
    "qurilish",
    "строительство",
    "монтаж",
    "проект",
    "стройматериалы",
    "оборудование",
    "ремонт",
    "сервис",
    
    # Infrastructure terms
    "infratuzilma",
    "инфраструктура",
    "yo'l",
    "doroga",
    "ko'prik",
    "most",
    "suv",
    "voda",
    "kanalizatsiya",
    "канализация",
    "elektr",
    "energiya",
    "энергия",
    
    # Industrial terms
    "ishlab chiqarish",
    "proizvodstvo",
    "sex",
    "tsex",
    "tsex",
    "цех",
    "laboratoriya",
    "лаборатория",
    "texnika",
    "texnika",
    "техника",
    
    # Agricultural terms
    "dehqonchilik",
    "zemledelie",
    "g'allakorlik",
    "zernovodstvo",
    "bog'dorchilik",
    "sadovodstvo",
    "chorvachilik",
    "zhivotnovodstvo",
    "parrandachilik",
    "ptitsevodstvo",
    
    # Storage/logistics terms
    "omborxona",
    "skladskoye",
    "logistika",
    "логистика",
    "transport",
    "транспорт",
    "yuk tashish",
    "gruzoperevozki",
    
    # English/international terms
    "construction",
    "delivery",
    "supply",
    "installation",
    "maintenance",
    "warehouse",
    "factory",
    "plant",
    "equipment",
    "materials",
]


def seed_keywords() -> None:
    db = SessionLocal()
    try:
        added = 0
        skipped = 0
        for phrase in INITIAL_KEYWORDS:
            existing = db.query(Keyword).filter(Keyword.phrase == phrase).first()
            if not existing:
                db.add(Keyword(phrase=phrase))
                added += 1
            else:
                skipped += 1

        db.commit()
        print(f"Seeded {added} keywords, skipped {skipped} duplicates.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_keywords()
