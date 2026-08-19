#!/usr/bin/env python3
"""Fix v0.3.1: pricing button visibility + sticky column mechanism"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(BASE, 'lib', 'client.js')
with open(CLIENT, 'r', encoding='utf-8') as f:
    text = f.read()

count = 0

# ══════════════════════════════════════════════════════════════════════
# 1. Fix CSS: panel should NOT scroll horizontally; table-wrap handles it
#    Also fix sticky: need border-left on cost cells for visual separation
# ══════════════════════════════════════════════════════════════════════
old_panel_css = "'#dsh-tu-modal .dsh-tu-panel{position:relative;z-index:1;width:920px;max-width:calc(100vw - 40px);max-height:82vh;overflow:auto;background:var(--dsw-alias-bg-layer-2, #ffffff);color:var(--dsw-alias-label-primary, #1f2937);border:1px solid var(--dsw-alias-line, rgba(0,0,0,.08));border-radius:16px;padding:18px 20px;box-shadow:0 18px 60px rgba(0,0,0,.22);}',"

new_panel_css = "'#dsh-tu-modal .dsh-tu-panel{position:relative;z-index:1;width:920px;max-width:calc(100vw - 40px);max-height:82vh;overflow-y:auto;overflow-x:hidden;background:var(--dsw-alias-bg-layer-2, #ffffff);color:var(--dsw-alias-label-primary, #1f2937);border:1px solid var(--dsw-alias-line, rgba(0,0,0,.08));border-radius:16px;padding:18px 20px;box-shadow:0 18px 60px rgba(0,0,0,.22);}',"

if old_panel_css in text:
    text = text.replace(old_panel_css, new_panel_css, 1)
    count += 1
    print("1. Panel: overflow-x:hidden, overflow-y:auto")

# Fix table-wrap CSS: add proper width constraint for sticky to work
old_wrap_css = "'#dsh-tu-modal .dsh-tu-table-wrap{overflow-x:auto;margin-top:6px;}',"
new_wrap_css = "'#dsh-tu-modal .dsh-tu-table-wrap{overflow-x:auto;margin-top:6px;position:relative;border:1px solid var(--dsw-alias-line, rgba(0,0,0,.06));border-radius:8px;}',"
if old_wrap_css in text:
    text = text.replace(old_wrap_css, new_wrap_css, 1)
    count += 1
    print("2. Table-wrap: added border + border-radius")

# Fix sticky cost-col: add left border for visual separation
old_sticky_css = "'#dsh-tu-modal th.dsh-tu-cost-col,#dsh-tu-modal td.dsh-tu-cost-col{position:sticky;right:0;z-index:2;background:var(--dsw-alias-bg-layer-2, #fff);border-left:1px solid var(--dsw-alias-line, rgba(0,0,0,.06));min-width:110px;}',"
new_sticky_css = "'#dsh-tu-modal th.dsh-tu-cost-col,#dsh-tu-modal td.dsh-tu-cost-col{position:sticky;right:0;z-index:2;background:inherit;border-left:2px solid var(--dsw-alias-line, rgba(0,0,0,.12));min-width:110px;padding-left:12px;padding-right:12px;}',"
if old_sticky_css in text:
    text = text.replace(old_sticky_css, new_sticky_css, 1)
    count += 1
    print("3. Cost-col: thicker border, inherit background")

# Fix th cost-col to also inherit background
old_th_cost = "'#dsh-tu-modal th.dsh-tu-cost-col{background:var(--dsw-alias-bg-layer-2, #fff);}',"
new_th_cost = "'#dsh-tu-modal th.dsh-tu-cost-col{background:var(--dsw-alias-bg-layer-1, #f7f7f8);}',"
if old_th_cost in text:
    text = text.replace(old_th_cost, new_th_cost, 1)
    count += 1
    print("4. th.dsh-tu-cost-col: header bg")

# ══════════════════════════════════════════════════════════════════════
# 2. Fix ⚙ button: use separate class, visible and distinct from ✕
# ══════════════════════════════════════════════════════════════════════
old_gear_btn = "html += '<button class=\"dsh-tu-close\" onclick=\"window.__dshTuTogglePricing && window.__dshTuTogglePricing()\" title=\"\\u81ea\\u5b9a\\u4e49\\u4ef7\\u683c\">\\u2699</button>';"
new_gear_btn = "html += '<button class=\"dsh-tu-settings-btn\" onclick=\"window.__dshTuTogglePricing && window.__dshTuTogglePricing()\" title=\"\\u81ea\\u5b9a\\u4e49\\u4ef7\\u683c\">\\u2699 \\u81ea\\u5b9a\\u4e49\\u4ef7\\u683c</button>';"
if old_gear_btn in text:
    text = text.replace(old_gear_btn, new_gear_btn, 1)
    count += 1
    print("5. Gear button: new class + text label")

# Add CSS for the settings button
old_actions_btn_css = "'#dsh-tu-modal .dsh-tu-actions button{border:1px solid var(--dsw-alias-line, rgba(0,0,0,.08));background:var(--dsw-alias-bg-layer-1, #f5f5f5);color:var(--dsw-alias-label-primary, #1f2937);border-radius:999px;padding:4px 10px;font-size:12px;cursor:pointer;}',"
new_actions_btn_css = "'#dsh-tu-modal .dsh-tu-actions button{border:1px solid var(--dsw-alias-line, rgba(0,0,0,.08));background:var(--dsw-alias-bg-layer-1, #f5f5f5);color:var(--dsw-alias-label-primary, #1f2937);border-radius:999px;padding:4px 10px;font-size:12px;cursor:pointer;}',\n          '#dsh-tu-modal .dsh-tu-settings-btn{border:1px solid var(--dsw-alias-line, rgba(0,0,0,.12));background:var(--dsw-alias-bg-layer-1, #f5f5f5);color:var(--dsw-alias-label-primary, #1f2937);border-radius:999px;padding:4px 12px;font-size:12px;cursor:pointer;white-space:nowrap;flex-shrink:0;}',\n          '#dsh-tu-modal .dsh-tu-settings-btn:hover{background:var(--dsw-alias-interactive-bg-hover, rgba(0,0,0,.06));}',"
if old_actions_btn_css in text:
    text = text.replace(old_actions_btn_css, new_actions_btn_css, 1)
    count += 1
    print("6. Added .dsh-tu-settings-btn CSS (pill button, visible)")

# ══════════════════════════════════════════════════════════════════════
# 3. Fix the head actions flex layout to prevent overflow
# ══════════════════════════════════════════════════════════════════════
old_head_css = "'#dsh-tu-modal .dsh-tu-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px;}',"
new_head_css = "'#dsh-tu-modal .dsh-tu-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px;flex-wrap:wrap;}',\n          '#dsh-tu-modal .dsh-tu-head h3{margin:0;font-size:16px;flex-shrink:0;}',"
if old_head_css in text:
    text = text.replace(old_head_css, new_head_css, 1)
    count += 1
    print("7. Head: flex-wrap + h3 flex-shrink")

# Remove duplicate h3 rule if it exists
dup_h3 = "'#dsh-tu-modal .dsh-tu-head h3{margin:0;font-size:16px;}',"
if dup_h3 in text:
    text = text.replace(dup_h3, '', 1)
    count += 1
    print("8. Removed duplicate h3 rule")

# ══════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════
print(f"\nApplied {count} fixes")
with open(CLIENT, 'w', encoding='utf-8') as f:
    f.write(text)
print("Saved!")
