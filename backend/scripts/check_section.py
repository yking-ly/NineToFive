"""Quick check for IPC Section 28"""
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = json.load(open('data/export_ipc.json', encoding='utf-8'))
matches = [d for d in data if d.get('metadata',{}).get('section_number') == '28']

print(f"Found {len(matches)} entries for section 28:")
for m in matches:
    lang = m['metadata']['language']
    doc = m['document'][:300].replace('\n', ' ')
    print(f"\n  [{lang}] {doc}...")
