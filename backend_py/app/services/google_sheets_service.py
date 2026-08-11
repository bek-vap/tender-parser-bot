"""
Google Sheets integration service for Tender Intelligence Platform
Automatically exports new tenders to Google Sheets in real-time
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.tender import Tender, Keyword, TenderKeywordMatch


class GoogleSheetsService:
    """Service for managing Google Sheets integration"""
    
    def __init__(self):
        self.scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = None
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Initialize Google Sheets credentials"""
        import os
        try:
            if settings.GOOGLE_SERVICE_ACCOUNT_JSON:
                # Use service account from environment
                credentials_info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
                self.credentials = Credentials.from_service_account_info(
                    credentials_info, 
                    scopes=self.scope
                )
            elif os.path.exists('google-credentials.json'):
                # Use service account file (for development)
                self.credentials = Credentials.from_service_account_file(
                    'google-credentials.json', 
                    scopes=self.scope
                )
            else:
                print("[WARNING] Google Sheets credentials not configured. Please set GOOGLE_SERVICE_ACCOUNT_JSON env var or place 'google-credentials.json' file.")
                self.credentials = None
                self.client = None
                return
            
            self.client = gspread.authorize(self.credentials)
            print("[SUCCESS] Google Sheets credentials initialized successfully")
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize Google Sheets credentials: {e}")
            self.credentials = None
            self.client = None
    
    def setup_spreadsheet(self, spreadsheet_name: str = "Tender Intelligence Platform") -> bool:
        """Setup or connect to Google Sheets spreadsheet"""
        if not self.client:
            return False
        try:
            # Try to open existing spreadsheet
            try:
                self.spreadsheet = self.client.open(spreadsheet_name)
                print(f"📊 Connected to existing spreadsheet: {spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                # Create new spreadsheet
                self.spreadsheet = self.client.create(spreadsheet_name)
                print(f"📊 Created new spreadsheet: {spreadsheet_name}")
                
                # Share with your email (optional)
                if settings.GOOGLE_SHEETS_SHARE_EMAIL:
                    self.spreadsheet.share(
                        settings.GOOGLE_SHEETS_SHARE_EMAIL,
                        perm_type='user',
                        role='writer'
                    )
            
            # Setup worksheet
            worksheet_name = "Tenders"
            try:
                self.worksheet = self.spreadsheet.worksheet(worksheet_name)
                print(f"📋 Connected to existing worksheet: {worksheet_name}")
            except gspread.WorksheetNotFound:
                self.worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows="1000",
                    cols="20"
                )
                self._setup_headers()
                print(f"📋 Created new worksheet: {worksheet_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup spreadsheet: {e}")
            return False
    
    def _setup_headers(self):
        """Setup worksheet headers"""
        headers = [
            "Tender nomi",
            "Kompaniya",
            "Telefon",
            "Email",
            "Summa",
            "Hudud",
            "Sana",
            "Link",
            "Source",
            "Keyword"
        ]
        
        self.worksheet.append_row(headers)
        print("📝 Headers setup completed")
    
    def export_tender(self, tender: Tender, keywords: List[str]) -> bool:
        """Export a single tender to Google Sheets"""
        if not self.worksheet:
            print("❌ Worksheet not initialized")
            return False
        
        try:
            row = [
                tender.title,
                tender.organizer_name or tender.source,
                tender.organizer_phone or "",
                tender.organizer_email or "",
                tender.amount or "",
                tender.region or "",
                tender.created_at.strftime("%Y-%m-%d %H:%M:%S") if tender.created_at else "",
                tender.url,
                tender.source,
                ", ".join(keywords)
            ]
            
            self.worksheet.append_row(row)
            print(f"✅ Exported tender to Google Sheets: {tender.title[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Failed to export tender: {e}")
            return False
    
    def export_tenders_batch(self, tenders_with_keywords: List[Dict[str, Any]]) -> int:
        """Export multiple tenders in batch"""
        if not self.worksheet:
            print("❌ Worksheet not initialized")
            return 0
        
        exported_count = 0
        
        try:
            # Prepare all rows
            rows = []
            for tender_data in tenders_with_keywords:
                tender = tender_data['tender']
                keywords = tender_data['keywords']
                
                row = [
                    tender.title,
                    tender.organizer_name or tender.source,
                    tender.organizer_phone or "",
                    tender.organizer_email or "",
                    tender.amount or "",
                    tender.region or "",
                    tender.created_at.strftime("%Y-%m-%d %H:%M:%S") if tender.created_at else "",
                    tender.url,
                    tender.source,
                    ", ".join(keywords)
                ]
                rows.append(row)
            
            # Append all rows at once
            if rows:
                self.worksheet.append_rows(rows)
                exported_count = len(rows)
                print(f"✅ Exported {exported_count} tenders to Google Sheets")
            
        except Exception as e:
            print(f"❌ Failed to export tenders batch: {e}")
        
        return exported_count
    
    def get_existing_tender_ids(self) -> set:
        """Get all existing tender IDs from Google Sheets to avoid duplicates"""
        if not self.worksheet:
            return set()
        
        try:
            # Get all data from column A (ID column)
            id_column = self.worksheet.col_values(1)
            # Skip header row
            tender_ids = set(id_column[1:]) if len(id_column) > 1 else set()
            print(f"📊 Found {len(tender_ids)} existing tenders in Google Sheets")
            return tender_ids
            
        except Exception as e:
            print(f"❌ Failed to get existing tender IDs: {e}")
            return set()
    
    def export_new_tenders(self, limit: int = 100) -> Dict[str, int]:
        """Export all new tenders with keyword matches to Google Sheets"""
        if not self.client or not self.worksheet:
            return {'processed': 0, 'exported': 0, 'skipped': 0}
        db = SessionLocal()
        try:
            # Get existing tender IDs from Google Sheets
            existing_ids = self.get_existing_tender_ids()
            
            # Find tenders with keyword matches that aren't in Google Sheets yet
            new_tenders_query = (
                db.query(Tender, Keyword)
                .join(TenderKeywordMatch)
                .join(Keyword)
                .filter(Keyword.is_active == True)
                .filter(~Tender.id.in_(existing_ids))
                .order_by(Tender.created_at.desc())
                .limit(limit)
            )
            
            # Group by tender and collect keywords
            tenders_dict = {}
            for tender, keyword in new_tenders_query:
                if tender.id not in tenders_dict:
                    tenders_dict[tender.id] = {
                        'tender': tender,
                        'keywords': []
                    }
                tenders_dict[tender.id]['keywords'].append(keyword.phrase)
            
            # Export to Google Sheets
            tenders_to_export = list(tenders_dict.values())
            exported_count = self.export_tenders_batch(tenders_to_export)
            
            return {
                'processed': len(tenders_to_export),
                'exported': exported_count,
                'skipped': len(tenders_to_export) - exported_count
            }
            
        except Exception as e:
            print(f"❌ Failed to export new tenders: {e}")
            return {'processed': 0, 'exported': 0, 'skipped': 0}
        finally:
            db.close()
    
    def get_spreadsheet_url(self) -> Optional[str]:
        """Get the URL of the spreadsheet"""
        if self.spreadsheet:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet.id}"
        return None
    
    def clear_all_data(self) -> bool:
        """Clear all data from worksheet (for testing/reset)"""
        if not self.worksheet:
            return False
        
        try:
            self.worksheet.clear()
            self._setup_headers()
            print("🗑️  Cleared all data from worksheet")
            return True
        except Exception as e:
            print(f"❌ Failed to clear worksheet: {e}")
            return False


# Global instance for reuse
_sheets_service = None

def get_google_sheets_service() -> GoogleSheetsService:
    """Get or create Google Sheets service instance"""
    global _sheets_service
    if _sheets_service is None:
        _sheets_service = GoogleSheetsService()
        # Auto-setup spreadsheet
        _sheets_service.setup_spreadsheet()
    return _sheets_service
