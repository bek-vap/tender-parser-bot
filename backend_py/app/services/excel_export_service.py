"""
Excel export service for Tender Intelligence Platform
Provides daily, weekly, and monthly tender exports in Excel format
"""

import io
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

import pandas as pd
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.tender import Tender, Keyword, TenderKeywordMatch


class ExcelExportService:
    """Service for exporting tenders to Excel format"""
    
    @staticmethod
    def get_tenders_with_keywords(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        with_keywords_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get tenders with their matched keywords. If with_keywords_only is False, returns all tenders."""
        db = SessionLocal()
        try:
            # We use a LEFT JOIN to include tenders even without keyword matches if requested
            query = (
                db.query(Tender, Keyword)
                .outerjoin(TenderKeywordMatch, Tender.id == TenderKeywordMatch.tender_id)
                .outerjoin(Keyword, Keyword.id == TenderKeywordMatch.keyword_id)
            )
            
            if with_keywords_only:
                # If we only want matches, filter where keyword is not null and active
                query = query.filter(Keyword.id != None, Keyword.is_active == True)
            
            if start_date:
                query = query.filter(Tender.created_at >= start_date)
            
            if end_date:
                query = query.filter(Tender.created_at <= end_date)
            
            query = query.order_by(Tender.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            # Group by tender and collect keywords
            tenders_dict = {}
            for tender, keyword in query:
                if tender.id not in tenders_dict:
                    tenders_dict[tender.id] = {
                        'id': tender.id,
                        'title': tender.title,
                        'description': tender.description or '',
                        'amount': tender.amount or '',
                        'region': tender.region or '',
                        'source': tender.source,
                        'url': tender.url,
                        'created_at': tender.created_at,
                        'external_id': tender.external_id or '',
                        'keywords': []
                    }
                if keyword and keyword.phrase:
                    tenders_dict[tender.id]['keywords'].append(keyword.phrase)
            
            tenders_list = list(tenders_dict.values())
            return tenders_list
            
        finally:
            db.close()
    
    @staticmethod
    def export_to_excel(
        tenders: List[Dict[str, Any]],
        filename_prefix: str = "tenders_export"
    ) -> bytes:
        """Export tenders to Excel format and return as bytes"""
        
        # Prepare data for DataFrame
        export_data = []
        for tender in tenders:
            export_data.append({
                'ID': tender['id'],
                'Tender Name': tender['title'],
                'Description': tender['description'][:500] if tender['description'] else '',  # Limit description
                'Company (Customer)': tender['source'],
                'Amount': tender['amount'],
                'Region': tender['region'],
                'Date': tender['created_at'].strftime('%Y-%m-%d %H:%M:%S') if tender['created_at'] else '',
                'Link': tender['url'],
                'Source': tender['source'],
                'External ID': tender['external_id'],
                'Keywords': ', '.join(tender['keywords']),
                'Keywords Count': len(tender['keywords'])
            })
        
        # Create DataFrame
        df = pd.DataFrame(export_data)
        
        # Create Excel writer with formatting
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main sheet
            df.to_excel(writer, sheet_name='Tenders', index=False)
            
            # Get worksheet for formatting
            worksheet = writer.sheets['Tenders']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)  # Cap at 50
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Create summary sheet
            summary_data = {
                'Metric': ['Total Tenders', 'Tenders with Keywords', 'Unique Keywords', 'Date Range', 'Export Generated'],
                'Value': [
                    len(tenders),
                    len([t for t in tenders if t['keywords']]),
                    len(set([kw for tender in tenders for kw in tender['keywords']])),
                    f"{tenders[0]['created_at'].strftime('%Y-%m-%d') if tenders else 'N/A'} to {tenders[-1]['created_at'].strftime('%Y-%m-%d') if tenders else 'N/A'}",
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Create keywords analysis sheet
            if tenders:
                all_keywords = {}
                for tender in tenders:
                    for keyword in tender['keywords']:
                        all_keywords[keyword] = all_keywords.get(keyword, 0) + 1
                
                keywords_data = {
                    'Keyword': list(all_keywords.keys()),
                    'Count': list(all_keywords.values()),
                    'Percentage': [round((count / len(tenders)) * 100, 2) for count in all_keywords.values()]
                }
                
                keywords_df = pd.DataFrame(keywords_data)
                keywords_df = keywords_df.sort_values('Count', ascending=False)
                keywords_df.to_excel(writer, sheet_name='Keywords Analysis', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def get_daily_export(date: Optional[datetime] = None) -> bytes:
        """Get daily export of tenders"""
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_date = date
        end_date = date + timedelta(days=1)
        
        tenders = ExcelExportService.get_tenders_with_keywords(
            start_date=start_date,
            end_date=end_date,
            with_keywords_only=False
        )
        
        filename_prefix = f"tenders_daily_{date.strftime('%Y%m%d')}"
        return ExcelExportService.export_to_excel(tenders, filename_prefix)
    
    @staticmethod
    def get_weekly_export(date: Optional[datetime] = None) -> bytes:
        """Get weekly export of tenders"""
        if date is None:
            date = datetime.now()
        
        # Get start of week (Monday)
        start_date = date - timedelta(days=date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        end_date = start_date + timedelta(days=7)
        
        tenders = ExcelExportService.get_tenders_with_keywords(
            start_date=start_date,
            end_date=end_date,
            with_keywords_only=False
        )
        
        filename_prefix = f"tenders_weekly_{start_date.strftime('%Y%m%d')}"
        return ExcelExportService.export_to_excel(tenders, filename_prefix)
    
    @staticmethod
    def get_monthly_export(date: Optional[datetime] = None) -> bytes:
        """Get monthly export of tenders"""
        if date is None:
            date = datetime.now()
        
        # Get start of month
        start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get start of next month
        if date.month == 12:
            end_date = date.replace(year=date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            end_date = date.replace(month=date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        tenders = ExcelExportService.get_tenders_with_keywords(
            start_date=start_date,
            end_date=end_date,
            with_keywords_only=False
        )
        
        filename_prefix = f"tenders_monthly_{date.strftime('%Y%m')}"
        return ExcelExportService.export_to_excel(tenders, filename_prefix)
    
    @staticmethod
    def get_custom_export(
        start_date: datetime,
        end_date: datetime,
        with_keywords_only: bool = True,
        limit: Optional[int] = None
    ) -> bytes:
        """Get custom date range export"""
        tenders = ExcelExportService.get_tenders_with_keywords(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            with_keywords_only=with_keywords_only
        )
        
        filename_prefix = f"tenders_custom_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
        return ExcelExportService.export_to_excel(tenders, filename_prefix)
    
    @staticmethod
    def get_export_statistics() -> Dict[str, Any]:
        """Get export statistics for the last 30 days"""
        db = SessionLocal()
        try:
            # Get date ranges
            now = datetime.now()
            
            # Daily stats
            daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            daily_end = daily_start + timedelta(days=1)
            
            # Weekly stats
            weekly_start = now - timedelta(days=now.weekday())
            weekly_start = weekly_start.replace(hour=0, minute=0, second=0, microsecond=0)
            weekly_end = weekly_start + timedelta(days=7)
            
            # Monthly stats
            monthly_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                monthly_end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                monthly_end = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Count tenders for each period
            def count_tenders_in_period(start, end):
                return (
                    db.query(Tender)
                    .join(TenderKeywordMatch, Tender.id == TenderKeywordMatch.tender_id)
                    .join(Keyword, Keyword.id == TenderKeywordMatch.keyword_id)
                    .filter(Keyword.is_active == True)
                    .filter(Tender.created_at >= start)
                    .filter(Tender.created_at < end)
                    .count()
                )
            
            stats = {
                'daily_count': count_tenders_in_period(daily_start, daily_end),
                'weekly_count': count_tenders_in_period(weekly_start, weekly_end),
                'monthly_count': count_tenders_in_period(monthly_start, monthly_end),
                'total_count': (
                    db.query(Tender)
                    .join(TenderKeywordMatch, Tender.id == TenderKeywordMatch.tender_id)
                    .join(Keyword, Keyword.id == TenderKeywordMatch.keyword_id)
                    .filter(Keyword.is_active == True)
                    .count()
                ),
                'last_export_date': now.strftime('%Y-%m-%d %H:%M:%S'),
                'periods': {
                    'daily': {
                        'start': daily_start.strftime('%Y-%m-%d %H:%M:%S'),
                        'end': daily_end.strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'weekly': {
                        'start': weekly_start.strftime('%Y-%m-%d %H:%M:%S'),
                        'end': weekly_end.strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'monthly': {
                        'start': monthly_start.strftime('%Y-%m-%d %H:%M:%S'),
                        'end': monthly_end.strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
            }
            
            return stats
            
        finally:
            db.close()
