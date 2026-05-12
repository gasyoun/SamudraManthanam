from web.ingest.parse_html import get_source_title
import os

path = "Index/lib/x86_64-win64/Data/Словарь Смирнова.txt"
if os.path.exists(path):
    try:
        title = get_source_title(path)
        print(f"Title: {title}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("File not found")
