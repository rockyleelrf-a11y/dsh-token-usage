#!/usr/bin/env python3
"""Apply v0.3.0: custom pricing with peak/off-peak + sticky cost column"""
import re, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT = os.path.join(BASE, 'lib', 'client.js')

with open(CLIENT, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Original size: {len(text):,} bytes, {text.count(chr(10))+1} lines")
applied = 0

# ══════════════════════════════════════════════════════════════════════
# 1. Add CUSTOM_PRICING_KEY + customPricing to state
# ══════════════════════════════════════════════════════════════════════
old_state = """      var CURRENCY_KEY = 'dsh-token-usage-currency';
      var state = {
        pricing: FALLBACK_PRICING,
        sessions: [],
        currentSession: null,
        currentModel: null,
        listError: null,
        detailed: null,
        detailedLoading: false,
        fx: FALLBACK_PRICING.cnyPerUsd,
        pricingSource: null
      };"""

new_state = """      var CURRENCY_KEY = 'dsh-token-usage-currency';
      var CUSTOM_PRICING_KEY = 'dsh-token-usage-custom-pricing';
      var state = {
        pricing: FALLBACK_PRICING,
        sessions: [],
        currentSession: null,
        currentModel: null,
        listError: null,
        detailed: null,
        detailedLoading: false,
        fx: FALLBACK_PRICING.cnyPerUsd,
        pricingSource: null,
        customPricing: {}
      };"""

if old_state in text:
    text = text.replace(old_state, new_state)
    applied += 1
    print("  + Added CUSTOM_PRICING_KEY and customPricing to state")

# ══════════════════════════════════════════════════════════════════════
# 2. Add custom pricing load/save functions + isPeakHour
# ══════════════════════════════════════════════════════════════════════
old_normalize = """      function normalizePrice(p) {
        return {
          input: Number(p.input || 0),
          output: Number(p.output || 0),
          cacheRead: Number(p.cacheRead || 0),
          cacheWrite: Number(p.cacheWrite || 0)
        };
      }"""

new_normalize = """      function normalizePrice(p) {
        return {
          input: Number(p.input || 0),
          output: Number(p.output || 0),
          cacheRead: Number(p.cacheRead || 0),
          cacheWrite: Number(p.cacheWrite || 0)
        };
      }

      function loadCustomPricing() {
        try {
          var raw = localStorage.getItem(CUSTOM_PRICING_KEY);
          if (raw) state.customPricing = JSON.parse(raw) || {};
        } catch (e) { state.customPricing = {}; }
      }

      function saveCustomPricing() {
        try {
          localStorage.setItem(CUSTOM_PRICING_KEY, JSON.stringify(state.customPricing));
        } catch (e) {}
      }

      function isPeakHour(rule) {
        if (!rule || !rule.peak || !rule.offPeak) return 'peak';
        var now = new Date();
        var h = now.getHours(), m = now.getMinutes();
        var mins = h * 60 + m;
        function toMins(t) {
          var p = t.split(':');
          return (parseInt(p[0]) || 0) * 60 + (parseInt(p[1]) || 0);
        }
        var pStart = toMins(rule.peak.start), pEnd = toMins(rule.peak.end);
        var oStart = toMins(rule.offPeak.start), oEnd = toMins(rule.offPeak.end);
        function inRange(s, e, v) {
          if (s <= e) return v >= s && v < e;
          return v >= s || v < e; // wraps midnight
        }
        if (inRange(pStart, pEnd, mins)) return 'peak';
        if (inRange(oStart, oEnd, mins)) return 'offPeak';
        return 'peak'; // default
      }

      function resolveCustomPrice(provider, model) {
        var key = provider ? provider + ':' + model : model;
        var entry = state.customPricing[key];
        if (!entry) {
          // try model-only key
          entry = state.customPricing[model];
        }
        if (!entry) return null;
        var phase = isPeakHour(entry);
        var src = entry[phase] || entry.peak || entry;
        if (src && typeof src === 'object' && ('input' in src || 'output' in src)) {
          return { input: Number(src.input || 0), output: Number(src.output || 0),
                   cacheRead: Number(src.cacheRead || 0), cacheWrite: Number(src.cacheWrite || 0),
                   _custom: true, _phase: phase };
        }
        return null;
      }"""

if old_normalize in text:
    text = text.replace(old_normalize, new_normalize)
    applied += 1
    print("  + Added loadCustomPricing, saveCustomPricing, isPeakHour, resolveCustomPrice")

# ══════════════════════════════════════════════════════════════════════
# 3. Modify resolvePrice to check custom pricing first
# ══════════════════════════════════════════════════════════════════════
old_resolve = """      function resolvePrice(provider, model) {
        if (!model) return null;
        var pm = state.pricing.providerModel || {};
        var entries = state.pricing.modelEntries || {};
        var alias = PROVIDER_ALIASES[provider] || provider;

        if (provider && pm[alias + ':' + model]) return normalizePrice(pm[alias + ':' + model]);
        if (provider && pm[provider + ':' + model]) return normalizePrice(pm[provider + ':' + model]);

        if (provider) {
          var hint = null;
          var prefixes = Object.keys(MODEL_PROVIDER_HINTS);
          for (var i = 0; i < prefixes.length; i++) {
            if (model.toLowerCase().indexOf(prefixes[i]) === 0) {
              hint = MODEL_PROVIDER_HINTS[prefixes[i]];
              break;
            }
          }
          if (hint && pm[hint + ':' + model]) return normalizePrice(pm[hint + ':' + model]);
        }

        if (!provider && entries[model] && entries[model].length) {
          var list = entries[model];
          for (var j = 0; j < list.length; j++) {
            var p = normalizePrice(list[j].price);
            if (p.input || p.output || p.cacheRead || p.cacheWrite) return p;
          }
          return normalizePrice(list[0].price);
        }

        // Built-in fallback for the two DeepSeek models this client ships with.
        if (FALLBACK_PRICING.providerModel['deepseek:' + model]) {
          return normalizePrice(FALLBACK_PRICING.providerModel['deepseek:' + model]);
        }
        return null;
      }"""

new_resolve = """      function resolvePrice(provider, model) {
        if (!model) return null;
        // Priority 1: user custom pricing (supports peak/off-peak)
        var custom = resolveCustomPrice(provider, model);
        if (custom) return custom;

        // Priority 2: DSH / plugin pricing database
        var pm = state.pricing.providerModel || {};
        var entries = state.pricing.modelEntries || {};
        var alias = PROVIDER_ALIASES[provider] || provider;

        if (provider && pm[alias + ':' + model]) return normalizePrice(pm[alias + ':' + model]);
        if (provider && pm[provider + ':' + model]) return normalizePrice(pm[provider + ':' + model]);

        if (provider) {
          var hint = null;
          var prefixes = Object.keys(MODEL_PROVIDER_HINTS);
          for (var i = 0; i < prefixes.length; i++) {
            if (model.toLowerCase().indexOf(prefixes[i]) === 0) {
              hint = MODEL_PROVIDER_HINTS[prefixes[i]];
              break;
            }
          }
          if (hint && pm[hint + ':' + model]) return normalizePrice(pm[hint + ':' + model]);
        }

        if (!provider && entries[model] && entries[model].length) {
          var list = entries[model];
          for (var j = 0; j < list.length; j++) {
            var p = normalizePrice(list[j].price);
            if (p.input || p.output || p.cacheRead || p.cacheWrite) return p;
          }
          return normalizePrice(list[0].price);
        }

        // Priority 3: built-in minimal fallback
        if (FALLBACK_PRICING.providerModel['deepseek:' + model]) {
          return normalizePrice(FALLBACK_PRICING.providerModel['deepseek:' + model]);
        }
        return null;
      }"""

if old_resolve in text:
    text = text.replace(old_resolve, new_resolve)
    applied += 1
    print("  + Modified resolvePrice: custom pricing -> database -> built-in")

# ══════════════════════════════════════════════════════════════════════
# 4. Add CSS for sticky cost column + scrollable table + pricing editor
# ══════════════════════════════════════════════════════════════════════
old_css_end = """          '#dsh-tu-modal .dsh-tu-loading{padding:24px;text-align:center;color:var(--dsw-alias-label-secondary, #6b7280);}'
        ].join('\\n');"""

new_css_end = """          '#dsh-tu-modal .dsh-tu-loading{padding:24px;text-align:center;color:var(--dsw-alias-label-secondary, #6b7280);}',
          '#dsh-tu-modal .dsh-tu-table-wrap{overflow-x:auto;margin-top:6px;}',
          '#dsh-tu-modal table{min-width:700px;}',
          '#dsh-tu-modal th.dsh-tu-cost-col,#dsh-tu-modal td.dsh-tu-cost-col{position:sticky;right:0;z-index:2;background:var(--dsw-alias-bg-layer-2, #fff);border-left:1px solid var(--dsw-alias-line, rgba(0,0,0,.06));min-width:110px;}',
          '#dsh-tu-modal th.dsh-tu-cost-col{background:var(--dsw-alias-bg-layer-2, #fff);}',
          '#dsh-tu-modal .dsh-tu-pricing-editor{background:var(--dsw-alias-bg-layer-1, #f7f7f8);border:1px solid var(--dsw-alias-line, rgba(0,0,0,.08));border-radius:10px;padding:14px;margin:10px 0;max-height:340px;overflow:auto;}',
          '#dsh-tu-modal .dsh-tu-pricing-editor textarea{width:100%;min-height:140px;font-family:monospace;font-size:11px;border:1px solid var(--dsw-alias-line, rgba(0,0,0,.12));border-radius:6px;padding:8px;resize:vertical;background:var(--dsw-alias-bg-layer-2, #fff);color:var(--dsw-alias-label-primary, #1f2937);}',
          '#dsh-tu-modal .dsh-tu-pricing-hint{font-size:11px;color:var(--dsw-alias-label-secondary, #6b7280);margin-top:6px;line-height:1.5;}',
          '#dsh-tu-modal .dsh-tu-pricing-actions{display:flex;gap:8px;margin-top:8px;}',
          '#dsh-tu-modal .dsh-tu-pricing-actions button{padding:5px 14px;border-radius:6px;font-size:12px;cursor:pointer;border:1px solid var(--dsw-alias-line, rgba(0,0,0,.1));}',
          '#dsh-tu-modal .dsh-tu-btn-primary{background:var(--dsw-alias-label-primary, #1f2937);color:var(--dsw-alias-bg-layer-2, #fff);border-color:transparent !important;}',
          '#dsh-tu-modal .dsh-tu-phase-tag{display:inline-block;font-size:10px;padding:1px 6px;border-radius:4px;margin-left:4px;vertical-align:middle;}',
          '#dsh-tu-modal .dsh-tu-phase-peak{background:#fef3c7;color:#92400e;}',
          '#dsh-tu-modal .dsh-tu-phase-offpeak{background:#d1fae5;color:#065f46;}'
        ].join('\\n');"""

if old_css_end in text:
    text = text.replace(old_css_end, new_css_end)
    applied += 1
    print("  + Added CSS: sticky cost column, scrollable tables, pricing editor")

# ══════════════════════════════════════════════════════════════════════
# 5. Add "自定义价格" button in modal header actions
# ══════════════════════════════════════════════════════════════════════
old_close_btn = """html += '<button class="dsh-tu-close" onclick="window.__dshTuClose && window.__dshTuClose()">\\u2715</button></div></div>';"""

new_close_btn = """html += '<button class="dsh-tu-close" onclick="window.__dshTuTogglePricing && window.__dshTuTogglePricing()" title="\\u81ea\\u5b9a\\u4e49\\u4ef7\\u683c">\\u2699</button>';
        html += '<button class="dsh-tu-close" onclick="window.__dshTuClose && window.__dshTuClose()">\\u2715</button></div></div>';"""

if old_close_btn in text:
    text = text.replace(old_close_btn, new_close_btn)
    applied += 1
    print("  + Added ⚙ custom pricing toggle button in modal header")

# ══════════════════════════════════════════════════════════════════════
# 6. Wrap tables in scrollable divs + sticky cost column
# ══════════════════════════════════════════════════════════════════════
# Model table: add scrollable wrapper + cost-col class
old_model_table_start = "html += '<table><thead><tr><th>\\u6a21\\u578b</th><th>Provider</th><th>\\u4f1a\\u8bdd\\u6570</th><th>\\u8f93\\u5165(\\u672a\\u7f13\\u5b58)</th><th>\\u7f13\\u5b58\\u8bfb\\u53d6</th><th>\\u7f13\\u5b58\\u5199\\u5165</th><th>\\u8f93\\u51fa</th><th>\\u4f30\\u7b97\\u8d39\\u7528</th></tr></thead><tbody>';"
new_model_table_start = "html += '<div class=\"dsh-tu-table-wrap\"><table><thead><tr><th>\\u6a21\\u578b</th><th>Provider</th><th>\\u4f1a\\u8bdd\\u6570</th><th>\\u8f93\\u5165(\\u672a\\u7f13\\u5b58)</th><th>\\u7f13\\u5b58\\u8bfb\\u53d6</th><th>\\u7f13\\u5b58\\u5199\\u5165</th><th>\\u8f93\\u51fa</th><th class=\"dsh-tu-cost-col\">\\u4f30\\u7b97\\u8d39\\u7528</th></tr></thead><tbody>';"

if old_model_table_start in text:
    text = text.replace(old_model_table_start, new_model_table_start, 1)
    applied += 1
    print("  + Model table: added scrollable wrapper + cost-col header")

# Model table: add cost-col class to row + close wrapper
old_model_close = """        });
        html += '</tbody></table>';"""

new_model_close = """        });
        html += '</tbody></table></div>';"""

# Find the model table close (first occurrence after d.models.forEach)
idx1 = text.find(old_model_close)
if idx1 > 0:
    text = text[:idx1] + new_model_close + text[idx1+len(old_model_close):]
    applied += 1
    print("  + Model table: closed scrollable wrapper")

# Session table: add scrollable wrapper + cost-col
old_sess_table_start = "html += '<table><thead><tr><th>\\u4f1a\\u8bdd / \\u6807\\u9898</th><th>\\u5de5\\u4f5c\\u533a</th><th>\\u6a21\\u578b</th><th>\\u8f93\\u5165(\\u672a\\u7f13\\u5b58)</th><th>\\u7f13\\u5b58\\u8bfb\\u53d6</th><th>\\u7f13\\u5b58\\u5199\\u5165</th><th>\\u8f93\\u51fa</th><th>\\u4f30\\u7b97\\u8d39\\u7528</th></tr></thead><tbody>';"
new_sess_table_start = "html += '<div class=\"dsh-tu-table-wrap\"><table><thead><tr><th>\\u4f1a\\u8bdd / \\u6807\\u9898</th><th>\\u5de5\\u4f5c\\u533a</th><th>\\u6a21\\u578b</th><th>\\u8f93\\u5165(\\u672a\\u7f13\\u5b58)</th><th>\\u7f13\\u5b58\\u8bfb\\u53d6</th><th>\\u7f13\\u5b58\\u5199\\u5165</th><th>\\u8f93\\u51fa</th><th class=\"dsh-tu-cost-col\">\\u4f30\\u7b97\\u8d39\\u7528</th></tr></thead><tbody>';"

if old_sess_table_start in text:
    text = text.replace(old_sess_table_start, new_sess_table_start, 1)
    applied += 1
    print("  + Session table: added scrollable wrapper + cost-col header")

# Session table: close wrapper (second occurrence)
idx2 = text.find(old_model_close, idx1 + 10) if idx1 > 0 else -1
if idx2 > 0:
    text = text[:idx2] + new_model_close + text[idx2+len(old_model_close):]
    applied += 1
    print("  + Session table: closed scrollable wrapper")

# ══════════════════════════════════════════════════════════════════════
# 7. Add dsh-tu-cost-col class to table data cells
# ══════════════════════════════════════════════════════════════════════
# Model row cost cell
old_model_cost = "html += '<td class=\"' + (unpriced ? 'dsh-tu-unpriced' : '') + '\">'"
new_model_cost = "html += '<td class=\"dsh-tu-cost-col' + (unpriced ? ' dsh-tu-unpriced' : '') + '\">'"
if old_model_cost in text:
    text = text.replace(old_model_cost, new_model_cost, 1)
    applied += 1
    print("  + Model row: cost cell gets sticky class")

# Session row cost cell - need to find the pattern
# The session row ends with: money(r.totals.cost) + '</td></tr>'
# Let's find it precisely
old_sess_cost = "money(r.totals.cost) + '</td></tr>';"
new_sess_cost = "money(r.totals.cost) + '</td></tr>';"
# Actually the session cost cell already doesn't have a class, so we add one
# Find: <td>' + money(r.totals.cost) + '</td></tr>
old_sess_cost_td = "'<td>' + money(r.totals.cost)"
new_sess_cost_td = "'<td class=\"dsh-tu-cost-col\">' + money(r.totals.cost)"
if old_sess_cost_td in text:
    text = text.replace(old_sess_cost_td, new_sess_cost_td, 1)
    applied += 1
    print("  + Session row: cost cell gets sticky class")

# ══════════════════════════════════════════════════════════════════════
# 8. Add pricing editor HTML + JS logic
# ══════════════════════════════════════════════════════════════════════
# Insert pricing editor div right after the source info line
old_source_end = """html += '<div class="dsh-tu-muted">\\u4ef7\\u683c\\u6765\\u6e90\\uff1a' + sourceLabel + '\\uff08USD / 1M tokens\\uff09\\uff0c\\u4ec5\\u542b\\u5df2\\u5b9a\\u4ef7\\u6a21\\u578b\\uff1b\\u6c47\\u7387 1 USD = ' + state.fx + ' CNY。</div>';"""

new_source_end = """html += '<div class="dsh-tu-muted">\\u4ef7\\u683c\\u6765\\u6e90\\uff1a' + sourceLabel + '\\uff08USD / 1M tokens\\uff09\\uff0c\\u4ec5\\u542b\\u5df2\\u5b9a\\u4ef7\\u6a21\\u578b\\uff1b\\u6c47\\u7387 1 USD = ' + state.fx + ' CNY。' + (state.pricingSource === 'peak' || state.pricingSource === 'offpeak' ? ' [' + state.pricingSource + ']' : '') + '</div>';
        // Pricing editor (hidden by default)
        html += '<div id="dsh-tu-pricing-editor" style="display:none;">';
        html += '<div class="dsh-tu-pricing-editor">';
        html += '<div style="font-size:13px;font-weight:600;margin-bottom:8px;">\\u81ea\\u5b9a\\u4e49\\u4ef7\\u683c\\u914d\\u7f6e</div>';
        html += '<div class="dsh-tu-pricing-hint">';
        html += '\\u683c\\u5f0f\\uff1a{ "provider:model": { "peak": {"input": ..., "output": ...}, "offPeak": {"input": ..., "output": ...}, "peakHours": {"start": "08:00", "end": "22:00"} } }<br>';
        html += '\\u4e5f\\u53ef\\u7b80\\u5355\\u8bbe\\u7f6e\\uff1a{ "provider:model": {"input": ..., "output": ..., "cacheRead": ..., "cacheWrite": ...} }<br>';
        html += '\\u4ef7\\u683c\\u5355\\u4f4d\\uff1aUSD / 1M tokens\\u3002\\u7559\\u7a7a\\u6216 0 \\u8868\\u793a\\u514d\\u8d39\\u3002';
        html += '</div>';
        html += '<textarea id="dsh-tu-pricing-textarea" placeholder="{}"></textarea>';
        html += '<div id="dsh-tu-pricing-error" style="color:#dc2626;font-size:11px;margin-top:4px;display:none;"></div>';
        html += '<div class="dsh-tu-pricing-actions">';
        html += '<button class="dsh-tu-btn-primary" onclick="window.__dshTuSavePricing && window.__dshTuSavePricing()">\\u4fdd\\u5b58</button>';
        html += '<button onclick="window.__dshTuResetPricing && window.__dshTuResetPricing()">\\u6e05\\u9664\\u6240\\u6709\\u81ea\\u5b9a\\u4e49</button>';
        html += '<button onclick="window.__dshTuExportPricing && window.__dshTuExportPricing()">\\u5bfc\\u51fa</button>';
        html += '<button onclick="window.__dshTuImportPricing && window.__dshTuImportPricing()">\\u5bfc\\u5165</button>';
        html += '</div>';
        html += '</div></div>';"""

if old_source_end in text:
    text = text.replace(old_source_end, new_source_end)
    applied += 1
    print("  + Added pricing editor HTML in modal")

# ══════════════════════════════════════════════════════════════════════
# 9. Add window API functions for pricing editor
# ══════════════════════════════════════════════════════════════════════
old_api = """      window.__dshTuSetCurrency = function (c) { setCurrency(c); };
      window.__dshTuClose = closeModal;"""

new_api = """      window.__dshTuSetCurrency = function (c) { setCurrency(c); };
      window.__dshTuClose = closeModal;

      // Pricing editor API
      window.__dshTuTogglePricing = function () {
        var editor = document.getElementById('dsh-tu-pricing-editor');
        if (!editor) return;
        var visible = editor.style.display !== 'none';
        editor.style.display = visible ? 'none' : 'block';
        if (!visible) {
          // populate textarea
          var ta = document.getElementById('dsh-tu-pricing-textarea');
          if (ta) ta.value = Object.keys(state.customPricing).length ? JSON.stringify(state.customPricing, null, 2) : '{}';
        }
      };

      window.__dshTuSavePricing = function () {
        var ta = document.getElementById('dsh-tu-pricing-textarea');
        var errEl = document.getElementById('dsh-tu-pricing-error');
        if (!ta) return;
        var raw = ta.value.trim() || '{}';
        try {
          var parsed = JSON.parse(raw);
          if (typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('\\u5fc5\\u987b\\u662f JSON \\u5bf9\\u8c61');
          // Validate each entry
          Object.keys(parsed).forEach(function (k) {
            var v = parsed[k];
            if (typeof v === 'object' && v !== null) {
              if (v.peak && typeof v.peak === 'object') {
                // peak/off-peak format - ok
              } else if ('input' in v || 'output' in v) {
                // simple format - ok
              } else {
                throw new Error(k + ': \\u65e0\\u6548\\u683c\\u5f0f');
              }
            }
          });
          state.customPricing = parsed;
          saveCustomPricing();
          if (errEl) errEl.style.display = 'none';
          refresh();
          // re-render modal to reflect new pricing
          if (state.detailed) {
            state.detailedLoading = false;
            loadDetailed().then(function () { renderModal(); });
          }
        } catch (e) {
          if (errEl) { errEl.textContent = '\\u683c\\u5f0f\\u9519\\u8bef\\uff1a' + e.message; errEl.style.display = 'block'; }
        }
      };

      window.__dshTuResetPricing = function () {
        state.customPricing = {};
        saveCustomPricing();
        var ta = document.getElementById('dsh-tu-pricing-textarea');
        if (ta) ta.value = '{}';
        var errEl = document.getElementById('dsh-tu-pricing-error');
        if (errEl) errEl.style.display = 'none';
        refresh();
        if (state.detailed) {
          state.detailedLoading = false;
          loadDetailed().then(function () { renderModal(); });
        }
      };

      window.__dshTuExportPricing = function () {
        var blob = new Blob([JSON.stringify(state.customPricing, null, 2)], { type: 'application/json' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'dsh-token-usage-pricing.json';
        a.click();
        URL.revokeObjectURL(a.href);
      };

      window.__dshTuImportPricing = function () {
        var input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = function (e) {
          var file = e.target.files[0];
          if (!file) return;
          var reader = new FileReader();
          reader.onload = function (ev) {
            var ta = document.getElementById('dsh-tu-pricing-textarea');
            if (ta) ta.value = ev.target.result;
            window.__dshTuSavePricing();
          };
          reader.readAsText(file);
        };
        input.click();
      };"""

if old_api in text:
    text = text.replace(old_api, new_api)
    applied += 1
    print("  + Added pricing editor API (toggle, save, reset, export, import)")

# ══════════════════════════════════════════════════════════════════════
# 10. Call loadCustomPricing on startup
# ══════════════════════════════════════════════════════════════════════
old_startup = """      injectStyle();
      loadPricing().then(function () {"""

new_startup = """      injectStyle();
      loadCustomPricing();
      loadPricing().then(function () {"""

if old_startup in text:
    text = text.replace(old_startup, new_startup)
    applied += 1
    print("  + Added loadCustomPricing() call on startup")

# ══════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════
print(f"\nApplied {applied}/10 changes")
print(f"Final size: {len(text):,} bytes, {text.count(chr(10))+1} lines")

with open(CLIENT, 'w', encoding='utf-8') as f:
    f.write(text)
print("Saved!")
