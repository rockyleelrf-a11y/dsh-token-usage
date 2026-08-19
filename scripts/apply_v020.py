#!/usr/bin/env python3
"""Apply all v0.2.0 optimizations to lib/client.js"""
import re, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(BASE, 'lib', 'client.js')

with open(CLIENT, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Original size: {len(text):,} bytes")

# ── 1. Replace loadPricing to add local pricing.json fallback ──────────
old_lp = re.search(
    r'function loadPricing\(\) \{.*?catch\(function \(\) \{[^}]*\}\);[^\n]*\n\s*\}',
    text, re.DOTALL
)
if old_lp:
    new_lp = '''function loadPricing() {
        // Chain: DSH assets -> plugin-local pricing.json -> minimal built-in
        return fetch('/assets/token-usage-pricing.json')
          .then(function (res) {
            if (!res.ok) throw new Error('dsh assets http ' + res.status);
            return res.json();
          })
          .then(function (p) {
            if (p && p.providerModel) {
              state.pricing = p;
              state.fx = p.cnyPerUsd || FALLBACK_PRICING.cnyPerUsd;
              state.pricingSource = 'dsh-assets';
              return;
            }
            throw new Error('invalid structure');
          })
          .catch(function () {
            // Fallback 1: plugin-local pricing.json
            return fetch(new URL('pricing.json', import.meta?.url || location.href).href)
              .then(function (res) { if (!res.ok) throw new Error('http ' + res.status); return res.json(); })
              .then(function (p) {
                if (p && p.providerModel) {
                  state.pricing = p;
                  state.fx = p.cnyPerUsd || FALLBACK_PRICING.cnyPerUsd;
                  state.pricingSource = 'plugin-local';
                  return;
                }
                throw new Error('invalid structure');
              })
              .catch(function () {
                // Fallback 2: minimal built-in (DeepSeek v4 only)
                state.pricing = FALLBACK_PRICING;
                state.fx = FALLBACK_PRICING.cnyPerUsd;
                state.pricingSource = 'builtin';
              });
          });
      }'''
    text = text[:old_lp.start()] + new_lp + text[old_lp.end():]
    print("  ✓ loadPricing updated with 3-tier fallback")
else:
    print("  ✗ loadPricing pattern not found")

# ── 2. Add pricingSource to state ──────────────────────────────────────
old_state = 'fx: FALLBACK_PRICING.cnyPerUsd\n      };'
new_state = 'fx: FALLBACK_PRICING.cnyPerUsd,\n        pricingSource: null\n      };'
if old_state in text:
    text = text.replace(old_state, new_state)
    print("  ✓ Added pricingSource to state")

# ── 3. Fix fragile settings button selector (add fallbacks) ────────────
old_fsb = """function findSettingsButton() {
        var buttons = document.querySelectorAll('button[aria-haspopup="dialog"]');
        for (var i = 0; i < buttons.length; i++) {
          var b = buttons[i];
          if (String(b.className || '').indexOf('VOzbGW_trigger') !== -1 || /设置|Settings/.test(b.textContent || '')) return b;
        }
        return buttons[0] || null;
      }"""

new_fsb = """function findSettingsButton() {
        // Try known selector patterns with graceful fallback
        var selectors = [
          'button[aria-haspopup="dialog"]',
          '.VOzbGW_trigger',
          'button[aria-label*="设置"], button[aria-label*="Settings"]'
        ];
        for (var s = 0; s < selectors.length; s++) {
          try {
            var btns = document.querySelectorAll(selectors[s]);
            for (var i = 0; i < btns.length; i++) {
              var text = btns[i].textContent || '';
              if (/设置|Settings|settings/i.test(text) || selectors[s].indexOf('VOzbGW') !== -1) return btns[i];
            }
            if (btns.length === 1) return btns[0];
          } catch (_) {}
        }
        // Last resort: any button whose text matches
        var all = document.querySelectorAll('button');
        for (var j = 0; j < all.length; j++) {
          if (/设置|Settings/.test(all[j].textContent || '')) return all[j];
        }
        return null;
      }"""

if old_fsb in text:
    text = text.replace(old_fsb, new_fsb)
    print("  ✓ findSettingsButton: added multi-selector fallback")

# ── 4. Fix fragile session selection selector ──────────────────────────
old_sel = """function detectSelectedSession(items) {
        try {
          var node = document.querySelector('[role="treeitem"][aria-selected="true"], .YDXeBa_selected');
          if (!node) return null;
          var text = node.textContent || '';"""

new_sel = """function detectSelectedSession(items) {
        try {
          var node = document.querySelector('[role="treeitem"][aria-selected="true"], .YDXeBa_selected, [data-selected="true"]');
          if (!node) return null;
          var text = node.textContent || '';"""

if old_sel in text:
    text = text.replace(old_sel, new_sel)
    print("  ✓ detectSelectedButton: added data-selected fallback")

# ── 5. Fix mountCard area selector (add fallbacks) ────────────────────
old_mount = """function mountCard() {
        var btn = findSettingsButton();
        if (!btn) return false;
        var area = btn.closest('.hHd-Xa_settingsArea') || btn.parentElement;
        if (!area || !area.parentElement) return false;
        if (!document.getElementById('dsh-tu-card')) {"""

new_mount = """function mountCard() {
        var btn = findSettingsButton();
        if (!btn) return false;
        var area = btn.closest('.hHd-Xa_settingsArea, [class*="settingsArea"], [class*="sidebar"]')
                   || btn.parentElement;
        if (!area || !area.parentElement) return false;
        if (!document.getElementById('dsh-tu-card')) {"""

if old_mount in text:
    text = text.replace(old_mount, new_mount)
    print("  ✓ mountCard: added multi-selector for settings area")

# ── 6. Add pricing-source badge to modal header ───────────────────────
old_modal_info = """html += '<div class="dsh-tu-muted">价格基于本地 pi-ai 价格库（USD / 1M tokens），仅含已定价模型；汇率 1 USD = ' + state.fx + ' CNY。</div>';"""

new_modal_info = """var sourceLabel = state.pricingSource === 'dsh-assets' ? 'DSH 内置价格库'
          : state.pricingSource === 'plugin-local' ? '插件内置价格库'
          : '最小化内置价格库（仅 DeepSeek v4）';
        html += '<div class="dsh-tu-muted">价格来源：' + sourceLabel + '（USD / 1M tokens），仅含已定价模型；汇率 1 USD = ' + state.fx + ' CNY。</div>';"""

if old_modal_info in text:
    text = text.replace(old_modal_info, new_modal_info)
    print("  ✓ Modal: pricing source badge added")

# ── 7. Add Ctrl+R shortcut to refresh detailed stats ──────────────────
old_esc = """document.addEventListener('keydown', function (e) {
          if (e.key === 'Escape') closeModal();
        });"""

new_esc = """document.addEventListener('keydown', function (e) {
          if (e.key === 'Escape') closeModal();
          if (e.key === 'r' && (e.ctrlKey || e.metaKey) && document.getElementById('dsh-tu-modal') && document.getElementById('dsh-tu-modal').classList.contains('dsh-tu-open')) {
            e.preventDefault();
            state.detailed = null;
            openModal();
          }
        });"""

if old_esc in text:
    text = text.replace(old_esc, new_esc)
    print("  ✓ Modal: Ctrl+R refresh shortcut added")

# ── 8. Fix refresh interval — clear previous timer to avoid stacking ──
old_interval = """refresh();
        setInterval(refresh, 30000);"""

new_interval = """refresh();
        if (window.__dshTuRefreshTimer) clearInterval(window.__dshTuRefreshTimer);
        window.__dshTuRefreshTimer = setInterval(refresh, 30000);"""

if old_interval in text:
    text = text.replace(old_interval, new_interval)
    print("  ✓ Refresh interval: no longer stacks multiple timers")

# ── 9. Add cache-write column to session stats table ──────────────────
old_sess_head = """html += '<th>输入(未缓存)</th><th>缓存读取</th><th>输出</th><th>估算费用</th></tr></thead><tbody>';
        d.rows.forEach(function (r) {
          var modelNames = (r.models || []).map(function (m) { return m.model; }).join(', ') || '\\u2014';
          html += '<tr><td>' + escapeHtml(r.title) + '</td><td class="dsh-tu-muted">' + escapeHtml(r.cwd) + '</td><td>' + escapeHtml(modelNames) + '</td><td>' + fmtInt(r.totals.input) + '</td><td>' + fmtInt(r.totals.cacheRead) + '</td><td>' + fmtInt(r.totals.output) + '</td><td>' + money(r.totals.cost) + '</td></tr>';"""

new_sess_head = """html += '<th>输入(未缓存)</th><th>缓存读取</th><th>缓存写入</th><th>输出</th><th>估算费用</th></tr></thead><tbody>';
        d.rows.forEach(function (r) {
          var modelNames = (r.models || []).map(function (m) { return m.model; }).join(', ') || '\\u2014';
          html += '<tr><td>' + escapeHtml(r.title) + '</td><td class="dsh-tu-muted">' + escapeHtml(r.cwd) + '</td><td>' + escapeHtml(modelNames) + '</td><td>' + fmtInt(r.totals.input) + '</td><td>' + fmtInt(r.totals.cacheRead) + '</td><td>' + fmtInt(r.totals.cacheWrite) + '</td><td>' + fmtInt(r.totals.output) + '</td><td>' + money(r.totals.cost) + '</td></tr>';"""

if old_sess_head in text:
    text = text.replace(old_sess_head, new_sess_head)
    print("  ✓ Session table: added cache-write column")

# ── 10. Add cache-write column to model stats table ───────────────────
old_model_head = """html += '<th>输入(未缓存)</th><th>缓存读取</th><th>输出</th><th>估算费用</th></tr></thead><tbody>';
        d.models.forEach(function (m) {"""

new_model_head = """html += '<th>输入(未缓存)</th><th>缓存读取</th><th>缓存写入</th><th>输出</th><th>估算费用</th></tr></thead><tbody>';
        d.models.forEach(function (m) {"""

if old_model_head in text:
    text = text.replace(old_model_head, new_model_head)
    print("  ✓ Model table: added cache-write header")

old_model_row = """html += '<tr><td>' + escapeHtml(m.model) + '</td><td class="dsh-tu-muted">' + escapeHtml(m.provider || '\\u2014') + '</td><td>' + m.sessions + '</td><td>' + fmtInt(m.input) + '</td><td>' + fmtInt(m.cacheRead) + '</td><td>' + fmtInt(m.output) + '</td><td class="' + (unpriced ? 'dsh-tu-unpriced' : '') + '">' + (unpriced ? '\\u672a\\u5b9a\\u4ef7/\\u514d\\u8d39' : money(m.cost)) + '</td></tr>';"""

new_model_row = """html += '<tr><td>' + escapeHtml(m.model) + '</td><td class="dsh-tu-muted">' + escapeHtml(m.provider || '\\u2014') + '</td><td>' + m.sessions + '</td><td>' + fmtInt(m.input) + '</td><td>' + fmtInt(m.cacheRead) + '</td><td>' + fmtInt(m.cacheWrite) + '</td><td>' + fmtInt(m.output) + '</td><td class="' + (unpriced ? 'dsh-tu-unpriced' : '') + '">' + (unpriced ? '\\u672a\\u5b9a\\u4ef7/\\u514d\\u8d39' : money(m.cost)) + '</td></tr>';"""

if old_model_row in text:
    text = text.replace(old_model_row, new_model_row)
    print("  ✓ Model table row: added cache-write cell")

# ── Done ───────────────────────────────────────────────────────────────
print(f"\nFinal size: {len(text):,} bytes ({len(text)/1024:.1f} KB)")

with open(CLIENT, 'w', encoding='utf-8') as f:
    f.write(text)

print("✓ lib/client.js saved")
