from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'templates'
pairs = [
    ('|date:"M d, Y H:i"', '|when:"full"'),
    ("|date:'M d, Y H:i'", "|when:'full'"),
    ('|date:"M d, Y"', '|when:"date"'),
    ('|date:"M d H:i"', '|when'),
    ('|date:"M d, H:i"', '|when'),
    ('|date:"M d"', '|when:"date"'),
    ('|date:"Y-m-d H:i"', '|when:"full"'),
]
changed = 0
for p in root.rglob('*.html'):
    text = p.read_text(encoding='utf-8')
    orig = text
    for a, b in pairs:
        text = text.replace(a, b)
    if text != orig:
        p.write_text(text, encoding='utf-8')
        changed += 1
        print(p)
print('changed', changed)
