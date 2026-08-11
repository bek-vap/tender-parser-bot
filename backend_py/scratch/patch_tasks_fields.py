import os

file_path = r'd:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py\app\workers\tasks.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update Tender instantiation in all scraping tasks to include organizer fields if available
patterns = [
    ('source=source,\n                external_id=it.external_id,', 'source=source,\n                external_id=it.external_id,\n                organizer_name=getattr(it, "organizer_name", None),\n                organizer_phone=getattr(it, "organizer_phone", None),\n                organizer_email=getattr(it, "organizer_email", None),'),
]

for old, new in patterns:
    content = content.replace(old, new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated tasks.py with organizer fields for all scrapers")
