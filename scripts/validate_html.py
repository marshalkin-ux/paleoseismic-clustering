"""Validate HTML and report stats."""
from html.parser import HTMLParser
import os
import json

class V(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []
    def handle_error(self, message):
        self.errors.append(message)

v = V()
v.feed(open('presentation/project_showcase.html', encoding='utf-8').read())
if v.errors:
    print('Parse errors:', v.errors)
else:
    print('HTML valid, no parse errors')

html_size = os.path.getsize('presentation/project_showcase.html')
json_size = os.path.getsize('presentation/map_data.json')
with open('presentation/map_data.json', encoding='utf-8') as f:
    data = json.load(f)

print(f'HTML size: {html_size:,} bytes ({html_size // 1024} KB)')
print(f'map_data.json size: {json_size:,} bytes ({json_size // 1024} KB)')
print(f'Events in map_data.json: {len(data["events"])}')
print(f'Total M>=6.5 events: {data["total"]}')

# Check map section present
with open('presentation/project_showcase.html', encoding='utf-8') as f:
    html = f.read()
print('Map section present:', 'id="map-section"' in html)
print('Leaflet CSS present:', 'leaflet@1.9.4/dist/leaflet.css' in html)
print('Leaflet JS present:', 'leaflet@1.9.4/dist/leaflet.js' in html)
print('Nav item present:', 'href="#map-section"' in html)
print('architecture section present:', 'id="architecture"' in html)
