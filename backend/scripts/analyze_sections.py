"""Analyze which IPC English sections are present/missing"""
import json
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

# Get project root (backend/scripts -> backend -> NineToFive)
project_root = Path(__file__).parent.parent.parent
data_file = project_root / 'data/export_ipc.json'
data = json.load(open(data_file, encoding='utf-8'))

# Get all English section numbers
en_sections = set()
for d in data:
    if d['metadata']['language'] == 'en':
        en_sections.add(d['metadata']['section_number'])

# Convert to integers where possible for proper sorting
def to_num(s):
    try:
        return int(s)
    except:
        return 999  # Put non-numeric at end

sorted_sections = sorted(en_sections, key=to_num)

print(f"Total English sections found: {len(sorted_sections)}")
print(f"\nFirst 20 sections: {sorted_sections[:20]}")
print(f"Last 20 sections: {sorted_sections[-20:]}")

# IPC has 511 sections (1-511)
expected = set(str(i) for i in range(1, 512))
missing = expected - en_sections
present = expected & en_sections

print(f"\n--- IPC COVERAGE ---")
print(f"Expected: 511 sections")
print(f"Present: {len(present)} sections")
print(f"Missing: {len(missing)} sections")

if missing:
    missing_sorted = sorted(missing, key=lambda x: int(x))
    print(f"\nMISSING SECTIONS ({len(missing_sorted)}):")
    # Print in groups of 20
    for i in range(0, len(missing_sorted), 20):
        print(f"  {missing_sorted[i:i+20]}")
