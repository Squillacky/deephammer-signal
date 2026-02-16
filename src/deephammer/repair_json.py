import json
from pathlib import Path

def repair_json(raw):
    fixed = raw.strip()
    for attempt in range(30):
        try:
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            pos = e.pos
            if pos is None:
                raise
            if pos > 0 and fixed[pos-1] == '"':
                fixed = fixed[:pos-1] + "'" + fixed[pos:]
            else:
                fixed = fixed[:pos] + fixed[pos+1:]
    return json.loads(fixed)

repaired = 0
base = Path('C:/Users/contr/projects/DeepHammer/data/analysis')
for p in base.glob('*.json'):
    d = json.load(open(p))
    if 'raw_response' not in d.get('analysis', {}):
        print('SKIP (already clean): ' + p.stem)
        continue
    raw = d['analysis']['raw_response']
    try:
        parsed = repair_json(raw)
        d['analysis'] = parsed
        with open(p, 'w') as f:
            json.dump(d, f, indent=2)
        repaired += 1
        hs = parsed.get('hook_anatomy',{}).get('hook_strength','?')
        print('REPAIRED: ' + p.stem + ' | hook_strength=' + str(hs))
    except Exception as e:
        print('FAILED: ' + p.stem + ' | ' + str(e))

print('Total repaired: ' + str(repaired) + '/3')
