#!/usr/bin/env python3
"""Fix row column order + add sticky cost classes"""
import os
CLIENT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib', 'client.js')
with open(CLIENT, 'r', encoding='utf-8') as f:
    text = f.read()
count = 0

# Model row: swap output/cacheWrite order, add cost-col class
a = "fmtInt(m.cacheRead) + '</td><td>' + fmtInt(m.output)"
b = " + '</td><td>' + fmtInt(m.cacheWrite)"
c = " + '</td><td class=\"' + (unpriced ? 'dsh-tu-unpriced' : '') + '\">'"
old_model = a + b + c
new_model = (
    "fmtInt(m.cacheRead) + '</td><td>' + fmtInt(m.cacheWrite)"
    " + '</td><td>' + fmtInt(m.output)"
    " + '</td><td class=\"dsh-tu-cost-col' + (unpriced ? ' dsh-tu-unpriced' : '') + '\">'"
)
if old_model in text:
    text = text.replace(old_model, new_model, 1)
    count += 1
    print("1. Model row: reorder + cost-col")

# Session row: swap output/cacheWrite order, add cost-col class
a2 = "fmtInt(r.totals.cacheRead) + '</td><td>' + fmtInt(r.totals.output)"
b2 = " + '</td><td>' + fmtInt(r.totals.cacheWrite)"
c2 = " + '</td><td>' + money(r.totals.cost) + '</td></tr>'"
old_sess = a2 + b2 + c2
new_sess = (
    "fmtInt(r.totals.cacheRead) + '</td><td>' + fmtInt(r.totals.cacheWrite)"
    " + '</td><td>' + fmtInt(r.totals.output)"
    " + '</td><td class=\"dsh-tu-cost-col\">' + money(r.totals.cost) + '</td></tr>'"
)
if old_sess in text:
    text = text.replace(old_sess, new_sess, 1)
    count += 1
    print("2. Session row: reorder + cost-col")

print(f"\nApplied {count} fixes")
with open(CLIENT, 'w', encoding='utf-8') as f:
    f.write(text)
print("Saved!")
