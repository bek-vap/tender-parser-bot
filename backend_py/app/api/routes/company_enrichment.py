from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.deps import get_db
from app.models.winner import CompanyProfile
from app.services.company_enrichment_service import get_company_enrichment_service

router = APIRouter(prefix="/company-enrichment", tags=["company-enrichment"])


class EnrichmentRequest(BaseModel):
    company_inn: str
    company_name: Optional[str] = None


@router.get("/statistics")
async def get_enrichment_statistics() -> Dict[str, Any]:
    """Get company enrichment statistics"""
    try:
        service = get_company_enrichment_service()
        stats = await service.get_enrichment_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/enrich")
async def enrich_single_company(
    request: EnrichmentRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Enrich a single company"""
    try:
        # Run enrichment in background
        background_tasks.add_task(
            _enrich_single_company_task,
            request.company_inn,
            request.company_name
        )
        
        return {
            "success": True,
            "message": f"Company enrichment started for INN: {request.company_inn}",
            "task": "background"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start enrichment: {str(e)}")


@router.post("/enrich-batch")
async def enrich_batch_companies(
    background_tasks: BackgroundTasks,
    limit: int = Query(10, ge=1, le=50)
) -> Dict[str, Any]:
    """Enrich multiple companies in batch"""
    try:
        # Run batch enrichment in background
        background_tasks.add_task(
            get_company_enrichment_service().enrich_multiple_companies,
            limit
        )
        
        return {
            "success": True,
            "message": f"Batch enrichment started for {limit} companies",
            "task": "background"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch enrichment: {str(e)}")


@router.get("/companies")
def get_unenriched_companies(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get companies that haven't been enriched yet"""
    try:
        companies = (
            db.query(CompanyProfile)
            .filter(CompanyProfile.is_enriched == False)
            .filter(CompanyProfile.company_inn.isnot(None))
            .order_by(CompanyProfile.total_wins.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        result = []
        for company in companies:
            result.append({
                "id": company.id,
                "company_name": company.company_name,
                "company_inn": company.company_inn,
                "total_wins": company.total_wins,
                "last_win_date": company.last_win_date.isoformat() if company.last_win_date else None,
                "created_at": company.created_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get companies: {str(e)}")


@router.get("/companies/enriched")
def get_enriched_companies(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get companies that have been enriched"""
    try:
        companies = (
            db.query(CompanyProfile)
            .filter(CompanyProfile.is_enriched == True)
            .order_by(CompanyProfile.enrichment_date.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        result = []
        for company in companies:
            result.append({
                "id": company.id,
                "company_name": company.company_name,
                "company_inn": company.company_inn,
                "phone": company.phone,
                "email": company.email,
                "website": company.website,
                "business_type": company.business_type,
                "specialization": company.specialization,
                "total_wins": company.total_wins,
                "enrichment_date": company.enrichment_date.isoformat() if company.enrichment_date else None,
                "enrichment_sources": company.enrichment_sources
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get enriched companies: {str(e)}")


@router.post("/companies/{company_id}/re-enrich")
async def re_enrich_company(
    company_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Re-enrich a specific company"""
    try:
        company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        if not company.company_inn:
            raise HTTPException(status_code=400, detail="Company has no INN for enrichment")
        
        # Reset enrichment status
        company.is_enriched = False
        company.enrichment_date = None
        company.enrichment_sources = None
        db.commit()
        
        # Run re-enrichment in background
        background_tasks.add_task(
            _enrich_single_company_task,
            company.company_inn,
            company.company_name
        )
        
        return {
            "success": True,
            "message": f"Re-enrichment started for company: {company.company_name}",
            "company_id": company_id,
            "company_inn": company.company_inn
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start re-enrichment: {str(e)}")


@router.get("/sources")
def get_enrichment_sources() -> Dict[str, Any]:
    """Get information about enrichment sources"""
    return {
        "sources": {
            "tax_database": {
                "name": "Tax Database",
                "description": "Official tax registration database",
                "data_fields": [
                    "director_name",
                    "registration_date", 
                    "legal_address",
                    "business_activities",
                    "tax_status"
                ],
                "availability": "Requires API access"
            },
            "google_search": {
                "name": "Google Search",
                "description": "Public web search results",
                "data_fields": [
                    "phone_numbers",
                    "email_addresses",
                    "website"
                ],
                "availability": "Public access"
            },
            "website_analysis": {
                "name": "Website Analysis",
                "description": "Direct analysis of company website",
                "data_fields": [
                    "phone_numbers",
                    "email_addresses",
                    "contact_forms",
                    "about_info"
                ],
                "availability": "Public access"
            }
        },
        "enrichment_process": [
            "1. Search tax database using company INN",
            "2. Perform Google search for company name",
            "3. Analyze company website if found",
            "4. Merge all data sources",
            "5. Update company profile with enriched data"
        ],
        "data_quality": {
            "high": ["Tax database", "Official website"],
            "medium": ["Google search results", "Social media"],
            "low": ["Third-party directories"]
        }
    }


@router.post("/test")
async def test_enrichment(
    company_inn: str = Query(...),
    company_name: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Test enrichment for a company without saving"""
    try:
        service = get_company_enrichment_service()
        enriched_data = await service.enrich_company(company_inn, company_name)
        
        return {
            "success": True,
            "enriched_data": {
                "inn": enriched_data.inn,
                "company_name": enriched_data.company_name,
                "director_name": enriched_data.director_name,
                "registration_date": enriched_data.registration_date,
                "legal_address": enriched_data.legal_address,
                "phone_numbers": enriched_data.phone_numbers,
                "email_addresses": enriched_data.email_addresses,
                "website": enriched_data.website,
                "business_activities": enriched_data.business_activities,
                "tax_status": enriched_data.tax_status,
                "employee_count": enriched_data.employee_count,
                "authorized_capital": enriched_data.authorized_capital
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def _enrich_single_company_task(company_inn: str, company_name: Optional[str] = None):
    """Background task for single company enrichment"""
    try:
        service = get_company_enrichment_service()
        enriched_data = await service.enrich_company(company_inn, company_name)
        await service.save_enriched_data(enriched_data)
        print(f"✅ Background enrichment completed for INN: {company_inn}")
        
    except Exception as e:
        print(f"❌ Background enrichment failed for INN {company_inn}: {e}")
        
        # Log error
        from app.services.logging_service import LoggingService
        LoggingService.log_task_failed(
            log_id="company_enrichment",
            error=e,
            message=f"Failed to enrich company with INN: {company_inn}",
            details={"company_inn": company_inn, "company_name": company_name}
        )
