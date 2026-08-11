from dataclasses import dataclass


@dataclass(frozen=True)
class KeywordDTO:
    id: str
    phrase: str
    is_blacklist: bool = False


class KeywordFilterService:
    def match(self, text: str, keywords: list[KeywordDTO]) -> list[str]:
        haystack = (text or "").lower()
        
        # 1. Check blacklist first (EXCLUSION)
        for k in keywords:
            if k.is_blacklist:
                needle = k.phrase.strip().lower()
                if needle and needle in haystack:
                    return []  # Immediate discard if any blacklist word matches
        
        # 2. Check regular keywords (INCLUSION)
        matched: list[str] = []
        for k in keywords:
            if not k.is_blacklist:
                needle = k.phrase.strip().lower()
                if needle and needle in haystack:
                    matched.append(k.id)

        return list(dict.fromkeys(matched))
