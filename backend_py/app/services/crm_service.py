import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings
from app.models.tender import Tender, Keyword

logger = logging.getLogger(__name__)

class CRMService:
    """
    Service for integrating with CRM systems.
    Sends tender leads to external CRM via webhooks or APIs.
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or getattr(settings, "CRM_WEBHOOK_URL", None)
        self.client = httpx.Client(timeout=10.0)

    def format_lead_data(self, tender: Tender, matched_keywords: List[Keyword]) -> Dict[str, Any]:
        """Format tender data for CRM submission"""
        return {
            "source_id": f"tender_{tender.id}",
            "title": tender.title,
            "company_name": tender.source,  # In this context, source is often the publisher/client
            "budget": tender.amount,
            "region": tender.region,
            "url": tender.url,
            "keywords": [kw.phrase for kw in matched_keywords],
            "status": "new_lead",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "external_id": tender.external_id,
                "source": tender.source
            }
        }

    async def send_lead(self, tender: Tender, matched_keywords: List[Keyword]) -> bool:
        """Send a new lead to the configured CRM"""
        lead_data = self.format_lead_data(tender, matched_keywords)
        
        # Log lead generation locally
        logger.info(f"Generated CRM lead for tender {tender.id}: {tender.title}")
        
        if not self.webhook_url:
            logger.warning("CRM_WEBHOOK_URL not configured, skipping external submission")
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=lead_data)
                response.raise_for_status()
                logger.info(f"Successfully sent lead {tender.id} to CRM")
                return True
        except Exception as e:
            logger.error(f"Failed to send lead to CRM: {e}")
            return False

    def close(self):
        self.client.close()

# Global instance
_crm_service = None

def get_crm_service() -> CRMService:
    global _crm_service
    if _crm_service is None:
        _crm_service = CRMService()
    return _crm_service
