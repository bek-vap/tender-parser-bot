import os

file_path = r'd:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py\app\workers\tasks.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update scrape_uzex_etender (if not already done)
if 'organizer_name=it.seller_name' not in content:
    content = content.replace(
        'url=f"https://etender.uzex.uz/lot/{it.id}",',
        'url=f"https://etender.uzex.uz/lot/{it.id}",\n                organizer_name=it.seller_name,'
    )

# 2. Add Google Sheets export to other tasks
export_block = """
        # Export to Google Sheets
        if settings.GOOGLE_SHEETS_AUTO_EXPORT:
            try:
                get_google_sheets_service().export_new_tenders(limit=50)
            except Exception as e:
                print(f"❌ Google Sheets export failed: {e}")
        
        LoggingService.log_task_complete("""

target = '        LoggingService.log_task_complete('

# We want to replace it in scrape_xarid_uzex, scrape_tender_mc, scrape_e_auksion
# But NOT in scrape_uzex_etender (it already has it) or process_winners/enrich_companies

tasks_to_patch = [
    'def scrape_xarid_uzex()',
    'def scrape_tender_mc()',
    'def scrape_e_auksion()'
]

for task in tasks_to_patch:
    if task in content:
        task_start = content.find(task)
        next_task_start = content.find('def ', task_start + 1)
        if next_task_start == -1: next_task_start = len(content)
        
        task_content = content[task_start:next_task_start]
        if 'get_google_sheets_service().export_new_tenders' not in task_content:
            new_task_content = task_content.replace(target, export_block)
            content = content[:task_start] + new_task_content + content[next_task_start:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully patched tasks.py")
