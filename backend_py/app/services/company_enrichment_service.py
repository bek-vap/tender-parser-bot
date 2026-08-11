"""
Company enrichment service for Tender Intelligence Platform
Gathers additional information about companies from various external sources
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.winner import Winner, CompanyProfile
from app.utils.inn import normalize_inn, is_generic_company_label, is_placeholder_company_name


@dataclass
class EnrichedCompanyData:
    """Data structure for enriched company information"""
    inn: str
    company_name: str
    director_name: Optional[str] = None
    registration_date: Optional[str] = None
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    phone_numbers: List[str] = None
    email_addresses: List[str] = None
    website: Optional[str] = None
    business_activities: List[str] = None
    tax_status: Optional[str] = None
    employee_count: Optional[int] = None
    authorized_capital: Optional[str] = None

    def __post_init__(self):
        if self.phone_numbers is None:
            self.phone_numbers = []
        if self.email_addresses is None:
            self.email_addresses = []
        if self.business_activities is None:
            self.business_activities = []


def lookup_company_name_in_db(inn: str) -> Optional[str]:
    """Winner / CompanyProfile by INN."""
    inn_key = normalize_inn(inn)
    if not inn_key:
        return None
    db = SessionLocal()
    try:
        winner = (
            db.query(Winner)
            .filter(Winner.company_inn == inn_key)
            .order_by(Winner.created_at.desc())
            .first()
        )
        if winner and winner.company_name and not is_placeholder_company_name(winner.company_name):
            return winner.company_name.strip()

        profile = (
            db.query(CompanyProfile)
            .filter(CompanyProfile.company_inn == inn_key)
            .first()
        )
        if profile and profile.company_name and not is_generic_company_label(profile.company_name, inn_key):
            return profile.company_name.strip()
    finally:
        db.close()
    return None


async def lookup_company_name_in_deals(inn: str, *, max_pages: int = 25) -> Optional[str]:
    """provider_name from DealsList for this INN."""
    from app.clients.uzex_etender_api import UzexEtenderApiClient

    inn_key = normalize_inn(inn)
    if not inn_key:
        return None

    api = UzexEtenderApiClient()
    try:
        page_size = 500
        for page in range(max_pages):
            from_ = page * page_size + 1
            to_ = from_ + page_size - 1
            try:
                deals = await api.deals_list(from_=from_, to=to_)
            except Exception:
                break
            if not deals:
                break
            for deal in deals:
                if not isinstance(deal, dict):
                    continue
                if normalize_inn(deal.get("provider_inn")) != inn_key:
                    continue
                name = (deal.get("provider_name") or "").strip()
                if name and not is_placeholder_company_name(name):
                    return name
            if len(deals) < page_size:
                break
    finally:
        await api.close()
    return None


class CompanyEnrichmentService:
    """Service for enriching company data from external sources"""

    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )

    async def enrich_company(
        self, company_inn: str, company_name: str = None
    ) -> EnrichedCompanyData:
        """Enrich company data from orginfo, DB, DealsList."""
        inn_key = normalize_inn(company_inn) or company_inn
        print(f"[*] Enriching company data for INN: {inn_key}")

        resolved_name = company_name
        if is_generic_company_label(resolved_name, inn_key):
            resolved_name = lookup_company_name_in_db(inn_key)

        result_data = EnrichedCompanyData(
            inn=inn_key,
            company_name=resolved_name or f"Компания {inn_key}",
        )

        try:
            org_data = await self._enrich_from_orginfo(inn_key)
            if org_data:
                result_data = self._merge_enriched_data(result_data, org_data)
        except Exception as e:
            print(f"[!] Orginfo enrichment failed: {e}")

        if is_generic_company_label(result_data.company_name, inn_key):
            db_name = lookup_company_name_in_db(inn_key)
            if db_name:
                result_data.company_name = db_name

        if is_generic_company_label(result_data.company_name, inn_key):
            deal_name = await lookup_company_name_in_deals(inn_key)
            if deal_name:
                result_data.company_name = deal_name

        try:
            search_term = (
                result_data.company_name
                if not is_generic_company_label(result_data.company_name, inn_key)
                else inn_key
            )
            google_data = await self._enrich_from_google_search(search_term)
            if google_data:
                result_data = self._merge_enriched_data(result_data, google_data)
        except Exception as e:
            print(f"[!] Google search failed: {e}")

        return result_data

    async def _parse_orginfo_with_page(self, page: Any, inn: str) -> Optional[EnrichedCompanyData]:
        """Orginfo search + profile using an existing Playwright page."""
        url = f"https://orginfo.uz/ru/search/organizations/?q={inn}"
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)

        search_hit = await page.evaluate(
            """() => {
                for (const a of document.querySelectorAll('a[href*="/organization/"]')) {
                    const name = (a.innerText || '').trim();
                    if (name.length > 2) {
                        return { href: a.href, name };
                    }
                }
                return null;
            }"""
        )

        company_name = (search_hit or {}).get("name")
        company_link = (search_hit or {}).get("href")
        director = None
        address = None
        activities: list[str] = []
        phones: list[str] = []
        emails: list[str] = []

        if company_link:
            await page.goto(company_link, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)

            extracted = await page.evaluate(
                        """() => {
                            const out = { name: null, legalName: null, director: null,
                                address: null, phones: [], emails: [] };

                            const pickOrg = (node) => {
                                if (!node) return null;
                                if (Array.isArray(node)) {
                                    for (const x of node) {
                                        const r = pickOrg(x);
                                        if (r) return r;
                                    }
                                    return null;
                                }
                                if (typeof node !== 'object') return null;
                                const t = node['@type'];
                                const types = Array.isArray(t) ? t : [t];
                                if (types.some(x => x && String(x).includes('Organization'))) {
                                    return node;
                                }
                                if (node['@graph']) return pickOrg(node['@graph']);
                                return null;
                            };

                            for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
                                try {
                                    const data = JSON.parse(script.innerText);
                                    const org = pickOrg(data);
                                    if (!org) continue;
                                    out.name = org.name || org.legalName || out.name;
                                    out.legalName = org.legalName || null;
                                    if (org.employee && org.employee.name) {
                                        out.director = org.employee.name;
                                    }
                                    if (org.address) {
                                        const loc = org.address.addressLocality || '';
                                        const street = org.address.streetAddress || '';
                                        out.address = [loc, street].filter(Boolean).join(', ');
                                    }
                                    if (org.telephone) out.phones.push(String(org.telephone));
                                    if (org.email) out.emails.push(String(org.email));
                                    break;
                                } catch (e) {}
                            }

                            const h1 = document.querySelector('h1[itemprop="name"], h1.h1-seo, h1');
                            if (h1 && h1.innerText.trim()) {
                                out.name = out.name || h1.innerText.trim();
                            }
                            const legal = document.querySelector('[itemprop="legalName"]');
                            if (legal && legal.innerText.trim()) {
                                out.legalName = legal.innerText.trim();
                            }
                            if (!out.name && out.legalName) {
                                out.name = out.legalName;
                            }
                            return out;
                        }"""
            )

            if extracted:
                company_name = (
                    extracted.get("legalName")
                    or extracted.get("name")
                    or company_name
                )
                director = extracted.get("director") or director
                address = extracted.get("address") or address
                phones = list(extracted.get("phones") or [])
                emails = list(extracted.get("emails") or [])

        final_name = (str(company_name).strip() if company_name else None)
        if final_name and is_generic_company_label(final_name, inn):
            final_name = None

        inn_key = normalize_inn(inn) or inn
        return EnrichedCompanyData(
            inn=inn_key,
            company_name=final_name or f"Компания {inn_key}",
            director_name=director,
            legal_address=address,
            business_activities=activities,
            phone_numbers=phones,
            email_addresses=emails,
        )

    async def _enrich_from_orginfo(self, inn: str) -> Optional[EnrichedCompanyData]:
        """Parse orginfo.uz: search + company profile (single INN, own browser)."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.http_client.headers.get("user-agent"),
                    viewport={"width": 1366, "height": 768},
                )
                page = await context.new_page()
                result = await self._parse_orginfo_with_page(page, inn)
                await context.close()
                await browser.close()
            return result
        except Exception as e:
            print(f"[!] Orginfo Playwright parse failed: {e}")
            return None

    async def enrich_companies_orginfo_batch(
        self,
        inns: list[str],
        *,
        on_progress: Any | None = None,
    ) -> dict[str, EnrichedCompanyData]:
        """One browser session for many INNs (Excel export)."""
        from playwright.async_api import async_playwright

        unique: list[str] = []
        seen: set[str] = set()
        for raw in inns:
            key = normalize_inn(raw) or str(raw).strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(key)

        results: dict[str, EnrichedCompanyData] = {}
        if not unique:
            return results

        total = len(unique)
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.http_client.headers.get("user-agent"),
                    viewport={"width": 1366, "height": 768},
                )
                page = await context.new_page()

                for i, inn in enumerate(unique, 1):
                    try:
                        data = await self._parse_orginfo_with_page(page, inn)
                        if data:
                            results[inn] = data
                            await self.upsert_enriched_data(data)
                    except Exception as e:
                        print(f"[!] Orginfo batch skip {inn}: {e}")

                    if on_progress and (i % 3 == 0 or i == total):
                        await on_progress(i, total)
                    if i % 5 == 0:
                        await asyncio.sleep(0.15)

                await context.close()
                await browser.close()
        except Exception as e:
            print(f"[!] Orginfo batch browser failed: {e}")

        return results

    async def _enrich_from_google_search(self, search_query: str) -> Optional[EnrichedCompanyData]:
        """Enrich from Google search results with Maps and Registry patterns"""
        try:
            queries = [
                f"{search_query} контактный телефон",
                f"{search_query} google maps 2gis",
                f"{search_query} stir direktor",
            ]

            all_content = ""
            for q in queries:
                search_url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
                response = await self.http_client.get(search_url)
                if response.status_code == 200:
                    all_content += response.text + " "
                await asyncio.sleep(1)

            phone_pattern = r"\+998\s?\(?\d{2}\)?\s?\d{3}\s?\d{2}\s?\d{2}"
            phones = re.findall(phone_pattern, all_content)

            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            emails = re.findall(email_pattern, all_content)

            website = None
            web_match = re.search(
                r"https?://(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)", all_content
            )
            if web_match:
                website = web_match.group(0)

            director = None
            director_match = re.search(
                r"(?:директор|director|rahbar):\s?([A-ZА-ЯЁ][a-zа-яё]+\s[A-ZА-ЯЁ][a-zа-яё]+)",
                all_content,
                re.IGNORECASE,
            )
            if director_match:
                director = director_match.group(1)

            name = search_query
            if is_generic_company_label(search_query):
                name = ""

            return EnrichedCompanyData(
                inn="",
                company_name=name,
                director_name=director,
                phone_numbers=list(set(phones))[:5],
                email_addresses=list(set(emails))[:5],
                website=website,
            )

        except Exception as e:
            print(f"[!] Enhanced Google search failed: {e}")
            return None

    async def _enrich_from_website(self, website_url: str) -> Optional[EnrichedCompanyData]:
        """Enrich from company website"""
        try:
            if not website_url.startswith(("http://", "https://")):
                website_url = "https://" + website_url

            response = await self.http_client.get(website_url)
            if response.status_code != 200:
                return None

            content = response.text.lower()

            phone_pattern = r"\+998\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}"
            phones = re.findall(phone_pattern, content)

            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            emails = re.findall(email_pattern, content)

            return EnrichedCompanyData(
                inn="",
                company_name="",
                phone_numbers=list(set(phones))[:5],
                email_addresses=list(set(emails))[:5],
                website=website_url,
            )

        except Exception as e:
            print(f"[!] Website enrichment failed for {website_url}: {e}")
            return None

    def _merge_enriched_data(
        self, base: EnrichedCompanyData, new: EnrichedCompanyData
    ) -> EnrichedCompanyData:
        """Merge new enrichment data into base data."""
        inn = base.inn or new.inn
        if new.company_name and not is_generic_company_label(new.company_name, inn):
            if is_generic_company_label(base.company_name, inn):
                base.company_name = new.company_name.strip()

        if new.director_name and not base.director_name:
            base.director_name = new.director_name

        if new.registration_date and not base.registration_date:
            base.registration_date = new.registration_date

        if new.legal_address and not base.legal_address:
            base.legal_address = new.legal_address

        if new.actual_address and not base.actual_address:
            base.actual_address = new.actual_address

        if new.phone_numbers:
            base.phone_numbers = list(set(base.phone_numbers + new.phone_numbers))

        if new.email_addresses:
            base.email_addresses = list(set(base.email_addresses + new.email_addresses))

        if new.website and not base.website:
            base.website = new.website

        if new.business_activities:
            base.business_activities = list(set(base.business_activities + new.business_activities))

        if new.tax_status and not base.tax_status:
            base.tax_status = new.tax_status

        if new.employee_count and not base.employee_count:
            base.employee_count = new.employee_count

        if new.authorized_capital and not base.authorized_capital:
            base.authorized_capital = new.authorized_capital

        return base

    async def upsert_enriched_data(self, enriched_data: EnrichedCompanyData) -> bool:
        """Create or update CompanyProfile (used after orginfo in export / check_inn)."""
        inn_key = normalize_inn(enriched_data.inn) or enriched_data.inn
        enriched_data.inn = inn_key

        db = SessionLocal()
        try:
            profile = db.query(CompanyProfile).filter(
                CompanyProfile.company_inn == inn_key
            ).first()

            if not profile:
                name = enriched_data.company_name
                if is_generic_company_label(name, inn_key):
                    name = lookup_company_name_in_db(inn_key) or f"Kompaniya {inn_key}"
                profile = CompanyProfile(
                    company_name=name,
                    company_inn=inn_key,
                )
                db.add(profile)

            if enriched_data.phone_numbers:
                profile.phone = enriched_data.phone_numbers[0]

            if enriched_data.email_addresses:
                profile.email = enriched_data.email_addresses[0]

            if enriched_data.website:
                profile.website = enriched_data.website

            if enriched_data.director_name:
                profile.business_type = f"Director: {enriched_data.director_name}"

            if enriched_data.business_activities:
                profile.specialization = ", ".join(enriched_data.business_activities[:3])

            if enriched_data.legal_address:
                profile.address = enriched_data.legal_address

            if enriched_data.company_name and not is_generic_company_label(
                enriched_data.company_name, inn_key
            ):
                profile.company_name = enriched_data.company_name

            profile.is_enriched = True
            profile.enrichment_date = datetime.utcnow()
            profile.enrichment_sources = json.dumps({
                "orginfo": bool(enriched_data.director_name or enriched_data.legal_address),
                "tax_database": bool(enriched_data.director_name),
                "google_search": bool(
                    enriched_data.phone_numbers or enriched_data.email_addresses
                ),
                "website_analysis": bool(enriched_data.website),
            })

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"[!] Error upserting enriched data: {e}")
            return False
        finally:
            db.close()

    async def save_enriched_data(self, enriched_data: EnrichedCompanyData) -> bool:
        """Save enriched data to company profile (creates profile if missing)."""
        return await self.upsert_enriched_data(enriched_data)

    async def enrich_multiple_companies(self, limit: int = 10) -> Dict[str, Any]:
        """Enrich companies that haven't been enriched yet."""
        db = SessionLocal()
        try:
            companies = (
                db.query(CompanyProfile)
                .filter(CompanyProfile.is_enriched == False)
                .filter(CompanyProfile.company_inn.isnot(None))
                .limit(limit)
                .all()
            )

            print(f"[*] Found {len(companies)} companies to enrich")

            enriched_count = 0
            errors = 0

            for company in companies:
                try:
                    enriched_data = await self.enrich_company(
                        company.company_inn,
                        company.company_name,
                    )
                    if await self.save_enriched_data(enriched_data):
                        enriched_count += 1
                except Exception as e:
                    errors += 1
                    print(f"[!] Error enriching company {company.company_name}: {e}")

            return {
                "companies_processed": len(companies),
                "enriched_successfully": enriched_count,
                "errors": errors,
                "success_rate": (enriched_count / len(companies)) * 100 if companies else 0,
            }
        finally:
            db.close()

    async def get_enrichment_statistics(self) -> Dict[str, Any]:
        """Get enrichment statistics."""
        db = SessionLocal()
        try:
            total_companies = db.query(CompanyProfile).count()
            enriched_companies = db.query(CompanyProfile).filter(
                CompanyProfile.is_enriched == True
            ).count()
            companies_with_inn = db.query(CompanyProfile).filter(
                CompanyProfile.company_inn.isnot(None)
            ).count()

            return {
                "total_companies": total_companies,
                "enriched_companies": enriched_companies,
                "companies_with_inn": companies_with_inn,
                "enrichment_rate": (
                    (enriched_companies / total_companies) * 100 if total_companies else 0
                ),
                "pending_enrichment": total_companies - enriched_companies,
            }
        finally:
            db.close()

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()


_company_enrichment_service = None


def get_company_enrichment_service() -> CompanyEnrichmentService:
    """Get or create company enrichment service instance"""
    global _company_enrichment_service
    if _company_enrichment_service is None:
        _company_enrichment_service = CompanyEnrichmentService()
    return _company_enrichment_service
