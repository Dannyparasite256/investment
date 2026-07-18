"""One-shot: apply |money filters across templates."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1] / 'templates'
changed = 0
for p in root.rglob('*.html'):
    text = p.read_text(encoding='utf-8')
    orig = text

    def repl_float(m):
        n = m.group(1)
        if n == '2':
            return '|money'
        return f'|money:{n}'

    text = re.sub(r'\|floatformat:(\d+)', repl_float, text)
    text = text.replace('|money|default:"0"', '|default:0|money')
    text = text.replace("|money|default:'0'", '|default:0|money')
    text = text.replace('|money|default:"0.00"', '|default:0|money')

    pairs = [
        (r'\{\{\s*d\.amount\s*\}\}', '{{ d.amount|money_trim:8 }}'),
        (r'\{\{\s*w\.amount\s*\}\}', '{{ w.amount|money_trim:8 }}'),
        (r'\{\{\s*t\.amount\s*\}\}', '{{ t.amount|money_trim:8 }}'),
        (r'\{\{\s*c\.amount\s*\}\}', '{{ c.amount|money_trim:8 }}'),
        (r'\{\{\s*e\.amount\s*\}\}', '{{ e.amount|money_trim:8 }}'),
        (r'\{\{\s*tx\.amount\s*\}\}', '{{ tx.amount|money_trim:8 }}'),
        (r'\{\{\s*inv\.amount\s*\}\}', '{{ inv.amount|money:2 }}'),
        (r'\{\{\s*inv\.total_earned\s*\}\}', '{{ inv.total_earned|money:2 }}'),
        (r'\{\{\s*deposit\.amount\s*\}\}', '{{ deposit.amount|money_trim:8 }}'),
        (r'\{\{\s*withdrawal\.amount\s*\}\}', '{{ withdrawal.amount|money_trim:8 }}'),
        (r'\{\{\s*withdrawal\.fee\s*\}\}', '{{ withdrawal.fee|money_trim:8 }}'),
        (r'\{\{\s*deposit\.credit_amount\s*\}\}', '{{ deposit.credit_amount|money:2 }}'),
        (r'\{\{\s*wallet\.available_balance\s*\}\}', '{{ wallet.available_balance|money:2 }}'),
        (r'\{\{\s*wallet\.balance\s*\}\}', '{{ wallet.balance|money:2 }}'),
        (r'\{\{\s*row\.w\.amount\s*\}\}', '{{ row.w.amount|money_trim:8 }}'),
        (r'\{\{\s*r\.deposit\.amount\s*\}\}', '{{ r.deposit.amount|money_trim:8 }}'),
        (r'\{\{\s*plan\.min_deposit\s*\}\}', '{{ plan.min_deposit|money:2 }}'),
        (r'\{\{\s*plan\.max_deposit\s*\}\}', '{{ plan.max_deposit|money:2 }}'),
        (r'\{\{\s*totals\.bal\s*\}\}', '{{ totals.bal|money:2 }}'),
        (r'\{\{\s*totals\.profit\s*\}\}', '{{ totals.profit|money:2 }}'),
        (r'\{\{\s*totals\.dep\s*\}\}', '{{ totals.dep|money:2 }}'),
        (r'\{\{\s*equity_now\s*\}\}', '{{ equity_now|money:2 }}'),
        (r'\{\{\s*total_invested\s*\}\}', '{{ total_invested|money:2 }}'),
        (r'\{\{\s*remaining\s*\}\}', '{{ remaining|money:2 }}'),
        (r'\{\{\s*stats\.total_earned\s*\}\}', '{{ stats.total_earned|money:2 }}'),
        (r'\{\{\s*stats\.paid\s*\}\}', '{{ stats.paid|money:2 }}'),
        (r'\{\{\s*e\.balance_after\s*\}\}', '{{ e.balance_after|money:2 }}'),
    ]
    for pat, rep in pairs:
        text = re.sub(pat, rep, text)

    # Avoid double-filtering
    text = text.replace('|money|money', '|money')
    text = text.replace('|money_trim:8|money_trim:8', '|money_trim:8')
    text = text.replace('|money:2|money:2', '|money:2')
    text = text.replace('|money:4|money:4', '|money:4')

    if text != orig:
        p.write_text(text, encoding='utf-8')
        changed += 1
        print('updated', p.relative_to(root.parent))
print('files_changed', changed)
