#!/usr/bin/env python3
"""Fix v0.3.2: remove built-in conflict guard, fix install mechanism"""
import os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(BASE, 'lib', 'client.js')
with open(CLIENT, 'r', encoding='utf-8') as f:
    text = f.read()

count = 0

# ══════════════════════════════════════════════════════════════════════
# 1. Remove the built-in conflict guard — our plugin replaces the
#    built-in token-usage-widget.js
# ══════════════════════════════════════════════════════════════════════
old_guard = """      if (window.__dshTokenUsageInstalled) return;
      window.__dshTokenUsageInstalled = true;"""
new_guard = """      // Override built-in token-usage-widget.js
      window.__dshTokenUsageInstalled = true;"""

if old_guard in text:
    text = text.replace(old_guard, new_guard, 1)
    count += 1
    print("1. Removed built-in conflict guard (our plugin overrides built-in)")

# ══════════════════════════════════════════════════════════════════════
# 2. Fix loadPricing: the pricing.json path should be absolute
#    based on the plugin's location, not relative
# ══════════════════════════════════════════════════════════════════════
old_fetch_local = "return fetch(new URL('pricing.json', import.meta?.url || location.href).href)"
new_fetch_local = "return fetch('/assets/token-usage-pricing.json').catch(function() { return fetch(new URL('pricing.json', document.currentScript?.src || location.href).href); })"

# Actually, let's try the built-in pricing.json path first (it exists in the app)
# Then fall back to our local one
old_chain = """          .catch(function () {
            // Fallback 1: plugin-local pricing.json
            return fetch(new URL('pricing.json', import.meta?.url || location.href).href)"""

new_chain = """          .catch(function () {
            // Fallback 1: try built-in pricing from app assets
            return fetch('/assets/token-usage-pricing.json')
              .then(function (res) { if (!res.ok) throw new Error('http ' + res.status); return res.json(); })
              .then(function (p) {
                if (p && p.providerModel) {
                  state.pricing = p;
                  state.fx = p.cnyPerUsd || FALLBACK_PRICING.cnyPerUsd;
                  state.pricingSource = 'dsh-builtin';
                  return;
                }
                throw new Error('invalid structure');
              })
              .catch(function () {
            // Fallback 2: plugin-local pricing.json
            return fetch(new URL('pricing.json', document.currentScript?.src || location.href).href)"""

if old_chain in text:
    text = text.replace(old_chain, new_chain, 1)
    count += 1
    print("2. Added DSH built-in pricing path to fallback chain")

# ══════════════════════════════════════════════════════════════════════
# 3. Fix the source label to recognize dsh-builtin
# ══════════════════════════════════════════════════════════════════════
old_source = "var sourceLabel = state.pricingSource === 'dsh-assets' ? 'DSH 内置价格库'"
new_source = "var sourceLabel = state.pricingSource === 'dsh-assets' || state.pricingSource === 'dsh-builtin' ? 'DSH 内置价格库'"
if old_source in text:
    text = text.replace(old_source, new_source, 1)
    count += 1
    print("3. Added dsh-builtin to source label mapping")

# ══════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════
print(f"\nApplied {count} fixes")
with open(CLIENT, 'w', encoding='utf-8') as f:
    f.write(text)
print("Saved!")
