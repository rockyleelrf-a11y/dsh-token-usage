#!/usr/bin/env python3
"""Apply remaining table column changes to client.js"""
import os, re

CLIENT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib', 'client.js')
with open(CLIENT, 'r', encoding='utf-8') as f:
    text = f.read()

count = 0

# 1. Model table row: add cacheWrite cell after cacheRead
old_model = re.search(
    r"(fmtInt\(m\.cacheRead\)\s*\+\s*'</td><td>'\s*\+\s*fmtInt\(m\.output\))",
    text
)
if old_model:
    text = text[:old_model.end()] + " + '</td><td>' + fmtInt(m.cacheWrite)" + text[old_model.end():]
    count += 1
    print("  + Model table row: cacheWrite cell")

# 2. Session table row: add cacheWrite cell after cacheRead
old_sess = re.search(
    r"(fmtInt\(r\.totals\.cacheRead\)\s*\+\s*'</td><td>'\s*\+\s*fmtInt\(r\.totals\.output\))",
    text
)
if old_sess:
    text = text[:old_sess.end()] + " + '</td><td>' + fmtInt(r.totals.cacheWrite)" + text[old_sess.end():]
    count += 1
    print("  + Session table row: cacheWrite cell")

# 3. Model table header: add cacheWrite column
old_mh = re.search(
    r"(\u7f13\u5b58\u8bfb\u53d6</th><th>\u8f93\u51fa</th><th>\u4f30\u7b97\u8d39\u7528</th></tr></thead><tbody>';\s*\n\s*d\.models\.forEach)",
    text
)
if old_mh:
    text = text[:old_mh.end(1)] + "\u7f13\u5b58\u5199\u5165</th><th>" + text[old_mh.end(1):]
    count += 1
    print("  + Model table header: cacheWrite column")

# 4. Session table header: add cacheWrite column (second occurrence)
all_mh = list(re.finditer(
    r"(\u7f13\u5b58\u8bfb\u53d6</th><th>\u8f93\u51fa</th><th>\u4f30\u7b97\u8d39\u7528</th></tr></thead><tbody>';\s*\n\s*d\.rows\.forEach)",
    text
))
for m in all_mh:
    text = text[:m.end(1)] + "\u7f13\u5b58\u5199\u5165</th><th>" + text[m.end(1):]
    count += 1
    print("  + Session table header: cacheWrite column")

print(f"\nApplied {count} changes")
print(f"File size: {len(text):,} bytes")

with open(CLIENT, 'w', encoding='utf-8') as f:
    f.write(text)
print("Saved!")
