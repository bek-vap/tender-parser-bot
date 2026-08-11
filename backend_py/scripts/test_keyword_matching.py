"""
Script to test keyword matching on real UZEX data
This helps validate the expanded keyword list and measure coverage
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List

from app.clients.uzex_etender_api import UzexEtenderApiClient
from app.db.session import SessionLocal
from app.models.tender import Keyword
from app.services.keyword_filter import KeywordFilterService


def test_keyword_matching():
    """Test keyword matching on real UZEX data"""
    print("🔍 Testing keyword matching on real UZEX data...")
    
    # Load keywords from database
    db = SessionLocal()
    try:
        keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
        print(f"📋 Loaded {len(keywords)} keywords from database")
        
        # Convert to DTO format
        keyword_dtos = [{"id": str(k.id), "phrase": k.phrase} for k in keywords]
        keyword_filter = KeywordFilterService()
        
    finally:
        db.close()
    
    # Fetch real data from UZEX
    api = UzexEtenderApiClient()
    try:
        print("🌐 Fetching real data from UZEX...")
        # Get more items for better testing
        items = api.trade_list(type_id=2, from_=1, to=100, system_id=0)
        print(f"📊 Retrieved {len(items)} tenders from UZEX")
        
    except Exception as e:
        print(f"❌ Failed to fetch data from UZEX: {e}")
        return
    finally:
        api.close()
    
    # Test keyword matching
    results = {
        "total_tenders": len(items),
        "matched_tenders": 0,
        "matches_by_keyword": {},
        "unmatched_samples": [],
        "matched_samples": []
    }
    
    print("\n🔍 Analyzing keyword matches...")
    
    for i, item in enumerate(items):
        # Combine title and region for better matching
        text_to_match = f"{item.name} {item.region_name or ''}"
        matched_ids = keyword_filter.match(text_to_match, keyword_dtos)
        
        if matched_ids:
            results["matched_tenders"] += 1
            
            # Get matched keyword phrases
            matched_keywords = []
            for kw in keywords:
                if str(kw.id) in matched_ids:
                    matched_keywords.append(kw.phrase)
                    if kw.phrase not in results["matches_by_keyword"]:
                        results["matches_by_keyword"][kw.phrase] = 0
                    results["matches_by_keyword"][kw.phrase] += 1
            
            # Store sample matches (first 10)
            if len(results["matched_samples"]) < 10:
                results["matched_samples"].append({
                    "title": item.name,
                    "region": item.region_name,
                    "matched_keywords": matched_keywords,
                    "cost": str(item.cost) if item.cost else None
                })
        else:
            # Store sample non-matches (first 10)
            if len(results["unmatched_samples"]) < 10:
                results["unmatched_samples"].append({
                    "title": item.name,
                    "region": item.region_name,
                    "cost": str(item.cost) if item.cost else None
                })
        
        # Progress indicator
        if (i + 1) % 20 == 0:
            print(f"Processed {i + 1}/{len(items)} tenders...")
    
    # Calculate coverage percentage
    coverage_percentage = (results["matched_tenders"] / results["total_tenders"]) * 100
    
    # Print results
    print("\n" + "="*60)
    print("📈 KEYWORD MATCHING TEST RESULTS")
    print("="*60)
    print(f"📊 Total tenders processed: {results['total_tenders']}")
    print(f"✅ Tenders with keyword matches: {results['matched_tenders']}")
    print(f"📈 Coverage percentage: {coverage_percentage:.2f}%")
    
    print(f"\n🔥 TOP 10 MATCHING KEYWORDS:")
    sorted_keywords = sorted(results["matches_by_keyword"].items(), key=lambda x: x[1], reverse=True)
    for i, (keyword, count) in enumerate(sorted_keywords[:10]):
        print(f"{i+1:2d}. {keyword:<25} - {count} matches")
    
    if results["matched_samples"]:
        print(f"\n✅ SAMPLE MATCHED TENDERS:")
        for i, sample in enumerate(results["matched_samples"][:5]):
            print(f"{i+1}. {sample['title'][:60]}...")
            print(f"   Keywords: {', '.join(sample['matched_keywords'])}")
            print()
    
    if results["unmatched_samples"]:
        print(f"❌ SAMPLE UNMATCHED TENDERS (potential new keywords):")
        for i, sample in enumerate(results["unmatched_samples"][:5]):
            print(f"{i+1}. {sample['title'][:60]}...")
            print()
    
    # Save detailed results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"keyword_matching_test_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"📁 Detailed results saved to: {results_file}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if coverage_percentage < 60:
        print("⚠️  Coverage is below 60%. Consider adding more keywords based on unmatched samples.")
    elif coverage_percentage < 80:
        print("📊 Coverage is good but could be improved. Analyze unmatched samples for new keywords.")
    else:
        print("🎉 Excellent coverage! The keyword list is working well.")
    
    return results


if __name__ == "__main__":
    test_keyword_matching()
