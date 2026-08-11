from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.deps import get_db
from app.models.winner import Winner, CompanyProfile
from app.services.winner_parser_service import get_winner_parser_service

router = APIRouter(prefix="/winners", tags=["winners"])


class WinnerResponse(BaseModel):
    id: str
    source: str
    tender_id: str
    tender_url: str
    company_name: str
    company_inn: Optional[str]
    company_address: Optional[str]
    company_phone: Optional[str]
    company_email: Optional[str]
    company_website: Optional[str]
    tender_amount: Optional[str]
    tender_date: Optional[datetime]
    winner_announcement_date: Optional[datetime]
    contract_details: Optional[str]
    competition_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyProfileResponse(BaseModel):
    id: str
    company_name: str
    company_inn: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    address: Optional[str]
    business_type: Optional[str]
    specialization: Optional[str]
    total_wins: int
    total_amount_won: Optional[str]
    first_win_date: Optional[datetime]
    last_win_date: Optional[datetime]
    is_enriched: bool
    enrichment_date: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("", response_model=List[WinnerResponse])
def list_winners(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    company_name: Optional[str] = Query(None),
    days_back: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db)
) -> List[Winner]:
    """List winners with optional filtering"""
    query = db.query(Winner)
    
    if company_name:
        query = query.filter(Winner.company_name.ilike(f"%{company_name}%"))
    
    if days_back:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(Winner.winner_announcement_date >= cutoff_date)
    
    return query.order_by(Winner.winner_announcement_date.desc()).offset(offset).limit(limit).all()


@router.get("/statistics")
def get_winner_statistics(
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get winner statistics"""
    try:
        parser_service = get_winner_parser_service()
        stats = parser_service.get_winner_statistics(days_back)
        
        # Add database statistics
        total_winners = db.query(Winner).count()
        total_companies = db.query(CompanyProfile).count()
        
        stats.update({
            "total_winners_all_time": total_winners,
            "total_companies_tracked": total_companies,
            "database_stats": {
                "winner_records": total_winners,
                "company_profiles": total_companies
            }
        })
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/top-companies")
def get_top_companies(
    limit: int = Query(20, ge=1, le=100),
    days_back: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get top companies by number of wins"""
    try:
        parser_service = get_winner_parser_service()
        top_companies = parser_service.get_top_companies(limit, days_back)
        
        # Format response
        formatted_companies = []
        for company in top_companies:
            formatted_companies.append({
                "company_name": company["company_name"],
                "company_inn": company["company_inn"],
                "total_wins": company["wins"],
                "total_amount": company["total_amount"],
                "first_win": company["first_win"].isoformat() if company["first_win"] else None,
                "last_win": company["last_win"].isoformat() if company["last_win"] else None
            })
        
        return formatted_companies
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top companies: {str(e)}")


@router.post("/parse")
def parse_winners(
    background_tasks: BackgroundTasks,
    days_back: int = Query(365, ge=0, le=3650)
) -> Dict[str, Any]:
    """Parse winners from completed tenders"""
    try:
        # Run parsing in background
        background_tasks.add_task(
            get_winner_parser_service().parse_completed_tenders,
            days_back
        )
        
        return {
            "success": True,
            "message": f"Winner parsing started for tenders from last {days_back} days",
            "task": "background"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start parsing: {str(e)}")


@router.get("/companies", response_model=List[CompanyProfileResponse])
def list_company_profiles(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    company_name: Optional[str] = Query(None),
    min_wins: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db)
) -> List[CompanyProfile]:
    """List company profiles"""
    query = db.query(CompanyProfile)
    
    if company_name:
        query = query.filter(CompanyProfile.company_name.ilike(f"%{company_name}%"))
    
    if min_wins:
        query = query.filter(CompanyProfile.total_wins >= min_wins)
    
    return query.order_by(CompanyProfile.total_wins.desc()).offset(offset).limit(limit).all()


@router.get("/companies/{company_id}", response_model=CompanyProfileResponse)
def get_company_profile(
    company_id: str,
    db: Session = Depends(get_db)
) -> CompanyProfile:
    """Get specific company profile"""
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")
    
    return company


@router.get("/companies/{company_id}/winners")
def get_company_winners(
    company_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> List[WinnerResponse]:
    """Get all wins for a specific company"""
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")
    
    winners = (
        db.query(Winner)
        .filter(
            (Winner.company_name == company.company_name) |
            (Winner.company_inn == company.company_inn)
        )
        .order_by(Winner.winner_announcement_date.desc())
        .limit(limit)
        .all()
    )
    
    return winners


@router.post("/companies/{company_id}/enrich")
def enrich_company_profile(
    company_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Enrich company profile with additional information"""
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company profile not found")
    
    try:
        # For now, this is a placeholder
        # In the future, this would integrate with external services
        # like tax databases, Google Maps, company websites, etc.
        
        background_tasks.add_task(
            self._enrich_company_data,
            company_id
        )
        
        return {
            "success": True,
            "message": "Company enrichment started in background",
            "company_id": company_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start enrichment: {str(e)}")


@router.delete("/{winner_id}")
def delete_winner(
    winner_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Delete a winner record"""
    winner = db.query(Winner).filter(Winner.id == winner_id).first()
    
    if not winner:
        raise HTTPException(status_code=404, detail="Winner not found")
    
    db.delete(winner)
    db.commit()
    
    return {
        "success": True,
        "message": "Winner deleted successfully"
    }


@router.get("/export/excel")
async def export_winners_excel(
    days_back: int = Query(0, ge=0, le=3650, description="0 = all winners in DB"),
):
    """Excel: monitored companies + won tenders (DealsList / winners DB)."""
    import io
    from fastapi.responses import StreamingResponse
    from app.services.winners_excel_export_service import WinnersExcelExportService

    try:
        if days_back == 0:
            excel_data, filename, count, _, _ = await WinnersExcelExportService.build_all_winners_export()
        else:
            excel_data, filename, count, _, _ = await WinnersExcelExportService.build_days_export(days_back)

        if not excel_data or count == 0:
            raise HTTPException(status_code=404, detail="No tenders to export")

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel export failed: {str(e)}")


@router.get("/export/csv")
def export_winners_csv(
    days_back: int = Query(30, ge=1, le=365),
    company_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Export winners to CSV format"""
    import csv
    from fastapi.responses import StreamingResponse
    import io
    
    query = db.query(Winner)
    
    if company_name:
        query = query.filter(Winner.company_name.ilike(f"%{company_name}%"))
    
    if days_back:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(Winner.winner_announcement_date >= cutoff_date)
    
    winners = query.order_by(Winner.winner_announcement_date.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'ID', 'Company Name', 'Company INN', 'Tender Amount', 'Tender Date',
        'Winner Announcement Date', 'Competition Type', 'Source', 'Tender URL'
    ])
    
    # Data
    for winner in winners:
        writer.writerow([
            winner.id,
            winner.company_name,
            winner.company_inn or '',
            winner.tender_amount or '',
            winner.tender_date.strftime('%Y-%m-%d') if winner.tender_date else '',
            winner.winner_announcement_date.strftime('%Y-%m-%d') if winner.winner_announcement_date else '',
            winner.competition_type or '',
            winner.source,
            winner.tender_url
        ])
    
    output.seek(0)
    
    filename = f"winners_export_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


async def _enrich_company_data(company_id: str):
    """Background task to enrich company data"""
    # Placeholder for company enrichment
    # This would integrate with external services
    pass
