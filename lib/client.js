window.__ModuleLoader__.load({
  id: "@deepseek-ai/dsh-token-usage",
  factory: (require) => {
    var module = { exports: {} };
    var exports = module.exports;
    Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });

    function apply(ctx) {

      'use strict';

      // Override built-in token-usage-widget.js
      window.__dshTokenUsageInstalled = true;

            var FALLBACK_PRICING = {
  "cnyPerUsd": 7.2,
  "unit": "USD / 1M tokens",
  "providerModel": {
    "deepseek:deepseek-v4-flash": {"input": 0.14, "output": 0.28, "cacheRead": 0.0028, "cacheWrite": 0.0},
    "deepseek:deepseek-v4-pro": {"input": 0.435, "output": 0.87, "cacheRead": 0.003625, "cacheWrite": 0.0}
  },
  "modelEntries": {
    "deepseek-v4-flash": [{"provider": "deepseek", "file": "deepseek", "price": {"input": 0.14, "output": 0.28, "cacheRead": 0.0028, "cacheWrite": 0.0}}],
    "deepseek-v4-pro": [{"provider": "deepseek", "file": "deepseek", "price": {"input": 0.435, "output": 0.87, "cacheRead": 0.003625, "cacheWrite": 0.0}}]
  }
};
var PROVIDER_ALIASES = {
        'deepseek-official': 'deepseek',
        'deepseek': 'deepseek',
        'zai-coding-cn': 'zai',
        'zai': 'zai',
        'qwen-token-plan-cn': 'qwen-token-plan-cn',
        'qwen-token-plan': 'qwen-token-plan'
      };

      var MODEL_PROVIDER_HINTS = {
        'deepseek': 'deepseek',
        'glm': 'zai',
        'qwen': 'qwen-token-plan-cn',
        'kimi': 'kimi-coding',
        'minimax': 'minimax-cn',
        'moonshot': 'moonshotai-cn'
      };

      var CURRENCY_KEY = 'dsh-token-usage-currency';
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
      };

      function el(tag, attrs, children) {
        var node = document.createElement(tag);
        if (attrs) {
          Object.keys(attrs).forEach(function (k) {
            if (k === 'class') node.className = attrs[k];
            else if (k === 'html') node.innerHTML = attrs[k];
            else if (k === 'text') node.textContent = attrs[k];
            else if (k === 'style') node.style.cssText = attrs[k];
            else node.setAttribute(k, attrs[k]);
          });
        }
        if (children) {
          (Array.isArray(children) ? children : [children]).forEach(function (c) {
            if (typeof c === 'string') node.appendChild(document.createTextNode(c));
            else if (c) node.appendChild(c);
          });
        }
        return node;
      }

      function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
          return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
      }

      function fmtInt(n) {
        return (Number(n) || 0).toLocaleString('en-US');
      }

      function currency() {
        try { return localStorage.getItem(CURRENCY_KEY) || 'cny'; } catch (e) { return 'cny'; }
      }
      function setCurrency(c) {
        try { localStorage.setItem(CURRENCY_KEY, c); } catch (e) {}
        renderCard();
        renderModal();
      }

      function usdToDisplay(usd) {
        if (currency() === 'cny') return usd * state.fx;
        return usd;
      }
      function money(usd) {
        var v = usdToDisplay(usd);
        if (currency() === 'cny') return '¥' + v.toFixed(4);
        return '$' + v.toFixed(4);
      }
      function moneyCompact(usd) {
        var v = usdToDisplay(usd);
        if (currency() === 'cny') return '¥' + v.toFixed(2);
        return '$' + v.toFixed(3);
      }

      function api(method, payload) {
        var rpcId = 'dsh-tu-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
        return fetch('/api/' + method, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type: 'client-request', rpcId: rpcId, method: method, payload: payload || {} })
        }).then(function (res) {
          if (!res.ok) throw new Error(method + ' HTTP ' + res.status);
          return res.json();
        }).then(function (data) {
          if (data && data.type === 'server-response' && data.result && data.result.ok) {
            return data.result.value;
          }
          throw new Error(method + ' failed: ' + (data && data.result && data.result.error ? data.result.error.message : 'unknown'));
        });
      }

      function loadPricing() {
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
            return fetch(new URL('pricing.json', document.currentScript?.src || location.href).href)
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
      }

      function normalizePrice(p) {
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
      }

      function resolvePrice(provider, model) {
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
      }

      function priceLabel(provider, model) {
        var p = resolvePrice(provider, model);
        if (!p) return '未定价';
        if (!p.input && !p.output && !p.cacheRead && !p.cacheWrite) return '未定价/免费';
        var u = money(p.input);
        return u + '/M';
      }

      function costForTokens(input, output, cacheRead, cacheWrite, provider, model) {
        var p = resolvePrice(provider, model);
        if (!p) return 0;
        return input / 1e6 * p.input + output / 1e6 * p.output + cacheRead / 1e6 * p.cacheRead + cacheWrite / 1e6 * p.cacheWrite;
      }

      function projectionTokens(s) {
        var v = (s.projections && s.projections.values && s.projections.values.tokenUsage) || {};
        return {
          input: Number(v.uncachedInputTokens || 0),
          output: Number(v.outputTokens || 0),
          cacheRead: Number(v.cacheReadTokens || 0),
          cacheWrite: Number(v.cacheWriteTokens || 0)
        };
      }
      function tokensTotal(t) {
        return (t.input || 0) + (t.output || 0) + (t.cacheRead || 0) + (t.cacheWrite || 0);
      }

      function blankSession(s) {
        var t = projectionTokens(s);
        return tokensTotal(t) === 0;
      }

      function chooseCurrentSession(items) {
        if (!items.length) return null;
        var selected = detectSelectedSession(items);
        if (selected) return selected;
        for (var i = 0; i < items.length; i++) if (items[i].running) return items[i];
        for (var j = 0; j < items.length; j++) if (!items[j].blank && items[j].cwd) return items[j];
        return items[0];
      }

      function detectSelectedSession(items) {
        try {
          var node = document.querySelector('[role="treeitem"][aria-selected="true"], .YDXeBa_selected, [data-selected="true"]');
          if (!node) return null;
          var text = node.textContent || '';
          // Prefer a title match; then a blank "new session" row.
          for (var i = 0; i < items.length; i++) {
            var title = items[i].projections && items[i].projections.values && items[i].projections.values.title;
            if (title && text.indexOf(title) !== -1) return items[i];
          }
          for (var j = 0; j < items.length; j++) {
            if (items[j].blank && /新会话|New session/i.test(text)) return items[j];
          }
          return null;
        } catch (e) {
          return null;
        }
      }

      function selectedSessionSignature() {
        try {
          var node = document.querySelector('[role="treeitem"][aria-selected="true"], .YDXeBa_selected');
          return node ? (node.textContent || '').trim() : '';
        } catch (e) {
          return '';
        }
      }

      function loadList() {
        return api('session.list', {}).then(function (value) {
          var items = (value && value.items) || [];
          state.sessions = items;
          state.listError = null;
          var cur = chooseCurrentSession(items);
          state.currentSession = cur;
          if (!cur) {
            state.currentModel = null;
            return;
          }
          return api('session.models', { sessionId: cur.sessionId }).then(function (m) {
            state.currentModel = (m && m.current) || null;
          }).catch(function () {
            state.currentModel = null;
          });
        }).catch(function (err) {
          state.listError = err;
          state.sessions = [];
          state.currentSession = null;
          state.currentModel = null;
        });
      }

      function fetchAllHistory(sessionId) {
        var all = [];
        var beforeSeq;
        var guard = 0;
        function page() {
          var payload = { sessionId: sessionId, maxMessages: 100000 };
          if (beforeSeq !== undefined) payload.beforeSeq = beforeSeq;
          return api('session.history', payload).then(function (v) {
            var events = (v && v.events) || [];
            for (var i = 0; i < events.length; i++) {
              if (events[i] && events[i].event) all.push(events[i].event);
            }
            if (v && v.hasMore && events.length && guard < 20) {
              beforeSeq = events[0].event.seq;
              guard++;
              return page();
            }
            return all;
          });
        }
        return page();
      }

      function parseHistoryEvents(session, events) {
        var currentRoute = null;
        var totals = { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, reasoning: 0, cost: 0 };
        var models = {};
        for (var i = 0; i < events.length; i++) {
          var ev = events[i];
          if (!ev) continue;
          var t = ev.type;
          var d = ev.data || {};
          if (t === 'request/header') {
            var cfg = (d.header && d.header.config) || {};
            if (cfg.model) currentRoute = { provider: cfg.provider || '', model: cfg.model };
          } else if (t === 'request/context') {
            if (d.model) currentRoute = { provider: d.provider || '', model: d.model };
          } else if (t === 'assistant/chunk') {
            var ch = d.chunk;
            if (!ch || ch.type !== 'usage') continue;
            var u = ch.usage || {};
            var input = Number(u.inputTokens || 0);
            var output = Number(u.outputTokens || 0);
            var cacheRead = Number(u.cacheReadTokens || 0);
            var cacheWrite = Number(u.cacheWriteTokens || 0);
            var reasoning = Number(u.reasoningTokens || 0);
            var provider = currentRoute ? currentRoute.provider : '';
            var model = currentRoute ? currentRoute.model : 'unknown';
            var key = provider ? provider + ':' + model : model;
            var cost = costForTokens(input, output, cacheRead, cacheWrite, provider, model);
            totals.input += input;
            totals.output += output;
            totals.cacheRead += cacheRead;
            totals.cacheWrite += cacheWrite;
            totals.reasoning += reasoning;
            totals.cost += cost;
            if (!models[key]) {
              models[key] = { provider: provider, model: model, input: 0, output: 0, cacheRead: 0, cacheWrite: 0, reasoning: 0, cost: 0, steps: 0 };
            }
            models[key].input += input;
            models[key].output += output;
            models[key].cacheRead += cacheRead;
            models[key].cacheWrite += cacheWrite;
            models[key].reasoning += reasoning;
            models[key].cost += cost;
            models[key].steps += 1;
          }
        }
        return {
          sessionId: session.sessionId,
          title: session.projections && session.projections.values && session.projections.values.title || session.cwd || session.sessionId,
          cwd: session.cwd || '',
          totals: totals,
          models: Object.keys(models).map(function (k) { return models[k]; }).sort(function (a, b) { return b.cost - a.cost || (b.input + b.output) - (a.input + a.output); })
        };
      }

      function loadDetailed() {
        if (state.detailedLoading) return Promise.resolve();
        state.detailedLoading = true;
        var candidates = state.sessions.filter(function (s) { return !blankSession(s); });
        var tasks = candidates.map(function (s) {
          return fetchAllHistory(s.sessionId)
            .then(function (events) { return parseHistoryEvents(s, events); })
            .catch(function (err) {
              var t = projectionTokens(s);
              return {
                sessionId: s.sessionId,
                title: (s.projections && s.projections.values && s.projections.values.title) || s.cwd || s.sessionId,
                cwd: s.cwd || '',
                totals: { input: t.input, output: t.output, cacheRead: t.cacheRead, cacheWrite: t.cacheWrite, reasoning: 0, cost: 0 },
                models: [],
                error: String(err && err.message || err)
              };
            });
        });
        return Promise.all(tasks).then(function (rows) {
          var modelMap = {};
          rows.forEach(function (row) {
            row.models.forEach(function (m) {
              var key = m.provider ? m.provider + ':' + m.model : m.model;
              if (!modelMap[key]) {
                modelMap[key] = { provider: m.provider, model: m.model, sessions: 0, input: 0, output: 0, cacheRead: 0, cacheWrite: 0, reasoning: 0, cost: 0 };
              }
              modelMap[key].sessions += 1;
              ['input', 'output', 'cacheRead', 'cacheWrite', 'reasoning', 'cost'].forEach(function (f) { modelMap[key][f] += m[f]; });
            });
          });
          var modelRows = Object.keys(modelMap).map(function (k) { return modelMap[k]; }).sort(function (a, b) {
            return b.cost - a.cost || (b.input + b.output) - (a.input + a.output);
          });
          var total = { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, reasoning: 0, cost: 0 };
          rows.forEach(function (r) {
            ['input', 'output', 'cacheRead', 'cacheWrite', 'reasoning', 'cost'].forEach(function (f) { total[f] += r.totals[f]; });
          });
          state.detailed = { rows: rows, models: modelRows, total: total };
          state.detailedLoading = false;
        }).catch(function (err) {
          state.detailedLoading = false;
          state.detailed = null;
          throw err;
        });
      }

      function findSettingsButton() {
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
      }

      function injectStyle() {
        if (document.getElementById('dsh-tu-style')) return;
        var css = [
          '#dsh-tu-card{box-sizing:border-box;width:100%;min-width:0;margin:0 0 12px;padding:10px 12px;border-radius:14px;cursor:pointer;background:var(--dsw-alias-bg-layer-2, rgba(255,255,255,.72));border:1px solid var(--dsw-alias-line, rgba(0,0,0,.08));color:var(--dsw-alias-label-primary, #1f2937);box-shadow:0 1px 2px rgba(0,0,0,.05);transition:background .15s, border-color .15s;}',
          '#dsh-tu-card:hover{background:var(--dsw-alias-interactive-bg-hover, rgba(0,0,0,.04));}',
          '#dsh-tu-card .dsh-tu-head{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:11px;color:var(--dsw-alias-label-secondary, #6b7280);margin-bottom:4px;}',
          '#dsh-tu-card .dsh-tu-model{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}',
          '#dsh-tu-card .dsh-tu-stats{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:4px;font-size:12px;color:var(--dsw-alias-label-secondary, #6b7280);}',
          '#dsh-tu-card .dsh-tu-stats b{color:var(--dsw-alias-label-primary, #1f2937);font-weight:600;}',
          '.hHd-Xa_collapsed #dsh-tu-card{padding:8px;margin-bottom:8px;text-align:center;width:auto;max-width:100%;}',
          '.hHd-Xa_collapsed #dsh-tu-card .dsh-tu-head .dsh-tu-arrow, .hHd-Xa_collapsed #dsh-tu-card .dsh-tu-stats .dsh-tu-hint{display:none;}',
          '.hHd-Xa_collapsed #dsh-tu-card .dsh-tu-model{font-size:11px;}',
          '#dsh-tu-modal{position:fixed;inset:0;z-index:9999;display:none;align-items:center;justify-content:center;}',
          '#dsh-tu-modal.dsh-tu-open{display:flex;}',
          '#dsh-tu-modal .dsh-tu-mask{position:absolute;inset:0;background:var(--dsw-alias-bg-mask-1, rgba(0,0,0,.45));backdrop-filter:var(--dsw-mask-blur, blur(4px));}',
          '#dsh-tu-modal .dsh-tu-panel{position:relative;z-index:1;width:920px;max-width:calc(100vw - 40px);max-height:82vh;overflow-y:auto;overflow-x:hidden;background:var(--dsw-alias-bg-layer-2, #ffffff);color:var(--dsw-alias-label-primary, #1f2937);border:1px solid var(--dsw-alias-line, rgba(0,0,0,.08));border-radius:16px;padding:18px 20px;box-shadow:0 18px 60px rgba(0,0,0,.22);}',
          '#dsh-tu-modal .dsh-tu-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px;flex-wrap:wrap;}',
          '#dsh-tu-modal .dsh-tu-head h3{margin:0;font-size:16px;flex-shrink:0;}',
          
          '#dsh-tu-modal .dsh-tu-close{border:1px solid var(--dsw-alias-line, rgba(0,0,0,.08));background:var(--dsw-alias-bg-layer-1, #f5f5f5);color:var(--dsw-alias-label-primary, #1f2937);border-radius:8px;width:28px;height:28px;cursor:pointer;}',
          '#dsh-tu-modal .dsh-tu-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:12px 0;}',
          '#dsh-tu-modal .dsh-tu-card-item{background:var(--dsw-alias-bg-layer-1, #f7f7f8);border:1px solid var(--dsw-alias-line, rgba(0,0,0,.06));border-radius:12px;padding:10px 12px;}',
          '#dsh-tu-modal .dsh-tu-card-item .k{font-size:11px;color:var(--dsw-alias-label-secondary, #6b7280);}',
          '#dsh-tu-modal .dsh-tu-card-item .v{font-size:18px;font-weight:700;margin-top:2px;}',
          '#dsh-tu-modal table{width:100%;border-collapse:collapse;font-size:12px;margin-top:6px;}',
          '#dsh-tu-modal th,#dsh-tu-modal td{text-align:right;padding:7px 8px;border-bottom:1px solid var(--dsw-alias-line, rgba(0,0,0,.07));white-space:nowrap;}',
          '#dsh-tu-modal th:first-child,#dsh-tu-modal td:first-child{text-align:left;}',
          '#dsh-tu-modal th{color:var(--dsw-alias-label-secondary, #6b7280);font-weight:600;}',
          '#dsh-tu-modal .dsh-tu-muted{color:var(--dsw-alias-label-secondary, #6b7280);}',
          '#dsh-tu-modal .dsh-tu-unpriced{color:#d97706;}',
          '#dsh-tu-modal .dsh-tu-actions{display:flex;gap:8px;align-items:center;}',
          '#dsh-tu-modal .dsh-tu-actions button{border:1px solid var(--dsw-alias-line, rgba(0,0,0,.08));background:var(--dsw-alias-bg-layer-1, #f5f5f5);color:var(--dsw-alias-label-primary, #1f2937);border-radius:999px;padding:4px 10px;font-size:12px;cursor:pointer;}',
          '#dsh-tu-modal .dsh-tu-settings-btn{border:1px solid var(--dsw-alias-line, rgba(0,0,0,.12));background:var(--dsw-alias-bg-layer-1, #f5f5f5);color:var(--dsw-alias-label-primary, #1f2937);border-radius:999px;padding:4px 12px;font-size:12px;cursor:pointer;white-space:nowrap;flex-shrink:0;}',
          '#dsh-tu-modal .dsh-tu-settings-btn:hover{background:var(--dsw-alias-interactive-bg-hover, rgba(0,0,0,.06));}',
          '#dsh-tu-modal .dsh-tu-actions button.dsh-tu-active{background:var(--dsw-alias-label-primary, #1f2937);color:var(--dsw-alias-bg-layer-2, #fff);}',
          '#dsh-tu-modal .dsh-tu-loading{padding:24px;text-align:center;color:var(--dsw-alias-label-secondary, #6b7280);}',
          '#dsh-tu-modal .dsh-tu-table-wrap{overflow-x:auto;margin-top:6px;position:relative;border:1px solid var(--dsw-alias-line, rgba(0,0,0,.06));border-radius:8px;}',
          '#dsh-tu-modal table{min-width:700px;}',
          '#dsh-tu-modal th.dsh-tu-cost-col,#dsh-tu-modal td.dsh-tu-cost-col{position:sticky;right:0;z-index:2;background:inherit;border-left:2px solid var(--dsw-alias-line, rgba(0,0,0,.12));min-width:110px;padding-left:12px;padding-right:12px;}',
          '#dsh-tu-modal th.dsh-tu-cost-col{background:var(--dsw-alias-bg-layer-1, #f7f7f8);}',
          '#dsh-tu-modal .dsh-tu-pricing-editor{background:var(--dsw-alias-bg-layer-1, #f7f7f8);border:1px solid var(--dsw-alias-line, rgba(0,0,0,.08));border-radius:10px;padding:14px;margin:10px 0;max-height:340px;overflow:auto;}',
          '#dsh-tu-modal .dsh-tu-pricing-editor textarea{width:100%;min-height:140px;font-family:monospace;font-size:11px;border:1px solid var(--dsw-alias-line, rgba(0,0,0,.12));border-radius:6px;padding:8px;resize:vertical;background:var(--dsw-alias-bg-layer-2, #fff);color:var(--dsw-alias-label-primary, #1f2937);}',
          '#dsh-tu-modal .dsh-tu-pricing-hint{font-size:11px;color:var(--dsw-alias-label-secondary, #6b7280);margin-top:6px;line-height:1.5;}',
          '#dsh-tu-modal .dsh-tu-pricing-actions{display:flex;gap:8px;margin-top:8px;}',
          '#dsh-tu-modal .dsh-tu-pricing-actions button{padding:5px 14px;border-radius:6px;font-size:12px;cursor:pointer;border:1px solid var(--dsw-alias-line, rgba(0,0,0,.1));}',
          '#dsh-tu-modal .dsh-tu-btn-primary{background:var(--dsw-alias-label-primary, #1f2937);color:var(--dsw-alias-bg-layer-2, #fff);border-color:transparent !important;}',
          '#dsh-tu-modal .dsh-tu-phase-tag{display:inline-block;font-size:10px;padding:1px 6px;border-radius:4px;margin-left:4px;vertical-align:middle;}',
          '#dsh-tu-modal .dsh-tu-phase-peak{background:#fef3c7;color:#92400e;}',
          '#dsh-tu-modal .dsh-tu-phase-offpeak{background:#d1fae5;color:#065f46;}'
        ].join('\n');
        var style = document.createElement('style');
        style.id = 'dsh-tu-style';
        style.textContent = css;
        document.head.appendChild(style);
      }

      function buildCard() {
        var card = el('div', { id: 'dsh-tu-card', title: '查看全部模型统计' });
        card.addEventListener('click', function () { openModal(); });
        renderCardContent(card);
        return card;
      }

      function renderCardContent(card) {
        if (!card) return;
        var cur = state.currentSession;
        var t = cur ? projectionTokens(cur) : { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 };
        var model = state.currentModel || { provider: '', model: '—' };
        var price = resolvePrice(model.provider, model.model);
        var unpriced = !price || (!price.input && !price.output && !price.cacheRead && !price.cacheWrite);
        var cost = costForTokens(t.input, t.output, t.cacheRead, t.cacheWrite, model.provider, model.model);
        var total = tokensTotal(t);
        var costText = total === 0 ? '暂无用量' : (unpriced ? '未定价' : moneyCompact(cost));
        card.innerHTML = [
          '<div class="dsh-tu-head"><span>Token 用量</span><span class="dsh-tu-arrow">↗</span></div>',
          '<div class="dsh-tu-model">' + escapeHtml(model.model) + '</div>',
          '<div class="dsh-tu-stats"><span>本会话 <b>' + (total ? fmtInt(total) : '0') + '</b></span><span>' + costText + '</span></div>'
        ].join('');
      }

      function renderCard() {
        var card = document.getElementById('dsh-tu-card');
        if (card) renderCardContent(card);
      }

      function buildModal() {
        var modal = el('div', { id: 'dsh-tu-modal' });
        modal.appendChild(el('div', { class: 'dsh-tu-mask' }));
        var panel = el('div', { class: 'dsh-tu-panel' });
        panel.id = 'dsh-tu-panel';
        modal.appendChild(panel);
        modal.querySelector('.dsh-tu-mask').addEventListener('click', closeModal);
        document.body.appendChild(modal);
        document.addEventListener('keydown', function (e) {
          if (e.key === 'Escape') closeModal();
          if (e.key === 'r' && (e.ctrlKey || e.metaKey) && document.getElementById('dsh-tu-modal') && document.getElementById('dsh-tu-modal').classList.contains('dsh-tu-open')) {
            e.preventDefault();
            state.detailed = null;
            openModal();
          }
        });
        return modal;
      }

      function openModal() {
        var modal = document.getElementById('dsh-tu-modal') || buildModal();
        modal.classList.add('dsh-tu-open');
        renderModal();
        if (!state.detailed && !state.detailedLoading) {
          var panel = document.getElementById('dsh-tu-panel');
          if (panel) panel.innerHTML = '<div class="dsh-tu-loading">正在加载完整会话记录并统计模型用量…</div>';
          loadDetailed().then(function () {
            renderModal();
          }).catch(function (err) {
            var panel = document.getElementById('dsh-tu-panel');
            if (panel) panel.innerHTML = '<div class="dsh-tu-loading">加载失败：' + escapeHtml(String(err && err.message || err)) + '</div>';
          });
        }
      }

      function closeModal() {
        var modal = document.getElementById('dsh-tu-modal');
        if (modal) modal.classList.remove('dsh-tu-open');
      }

      function renderModal() {
        var panel = document.getElementById('dsh-tu-panel');
        if (!panel) return;
        var d = state.detailed;
        var html = '';
        html += '<div class="dsh-tu-head"><h3>Token 用量与费用统计</h3><div class="dsh-tu-actions">';
        html += '<button class="' + (currency() === 'cny' ? 'dsh-tu-active' : '') + '" onclick="window.__dshTuSetCurrency && window.__dshTuSetCurrency(\'cny\')">¥ CNY</button>';
        html += '<button class="' + (currency() === 'usd' ? 'dsh-tu-active' : '') + '" onclick="window.__dshTuSetCurrency && window.__dshTuSetCurrency(\'usd\')">$ USD</button>';
        html += '<button class="dsh-tu-settings-btn" onclick="window.__dshTuTogglePricing && window.__dshTuTogglePricing()" title="自定义价格">⚙ 自定义价格</button>';
        html += '<button class="dsh-tu-close" onclick="window.__dshTuClose && window.__dshTuClose()">✕</button></div></div>';
        var sourceLabel = state.pricingSource === 'dsh-assets' || state.pricingSource === 'dsh-builtin' ? 'DSH 内置价格库'
          : state.pricingSource === 'plugin-local' ? '插件内置价格库'
          : '最小化内置价格库（仅 DeepSeek v4）';
        html += '<div class="dsh-tu-muted">价格来源：' + sourceLabel + '（USD / 1M tokens），仅含已定价模型；汇率 1 USD = ' + state.fx + ' CNY。</div>';
        if (!d) {
          html += '<div class="dsh-tu-loading">暂无完整统计。点击卡片后自动加载。</div>';
          panel.innerHTML = html;
          return;
        }
        html += '<div class="dsh-tu-cards">';
        html += '<div class="dsh-tu-card-item"><div class="k">总会话数</div><div class="v">' + d.rows.length + '</div></div>';
        html += '<div class="dsh-tu-card-item"><div class="k">总 Token</div><div class="v">' + fmtInt(tokensTotal(d.total)) + '</div></div>';
        html += '<div class="dsh-tu-card-item"><div class="k">输入 (未缓存)</div><div class="v">' + fmtInt(d.total.input) + '</div></div>';
        html += '<div class="dsh-tu-card-item"><div class="k">缓存读取</div><div class="v">' + fmtInt(d.total.cacheRead) + '</div></div>';
        html += '<div class="dsh-tu-card-item"><div class="k">缓存写入</div><div class="v">' + fmtInt(d.total.cacheWrite) + '</div></div>';
        html += '<div class="dsh-tu-card-item"><div class="k">输出</div><div class="v">' + fmtInt(d.total.output) + '</div></div>';
        html += '<div class="dsh-tu-card-item"><div class="k">估算费用</div><div class="v">' + money(d.total.cost) + '</div></div>';
        html += '</div>';

        html += '<h3 style="font-size:14px;margin:14px 0 6px;">按模型统计</h3>';
        html += '<div class="dsh-tu-table-wrap"><table><thead><tr><th>模型</th><th>Provider</th><th>会话数</th><th>输入(未缓存)</th><th>缓存读取</th><th>缓存写入</th><th>输出</th><th class="dsh-tu-cost-col">估算费用</th></tr></thead><tbody>';
        d.models.forEach(function (m) {
          var p = resolvePrice(m.provider, m.model);
          var unpriced = !p || (!p.input && !p.output && !p.cacheRead && !p.cacheWrite);
          html += '<tr><td>' + escapeHtml(m.model) + '</td><td class="dsh-tu-muted">' + escapeHtml(m.provider || '—') + '</td><td>' + m.sessions + '</td><td>' + fmtInt(m.input) + '</td><td>' + fmtInt(m.cacheRead) + '</td><td>' + fmtInt(m.cacheWrite) + '</td><td>' + fmtInt(m.output) + '</td><td class="dsh-tu-cost-col' + (unpriced ? ' dsh-tu-unpriced' : '') + '">' + (unpriced ? '未定价/免费' : money(m.cost)) + '</td></tr>';
        });
        html += '</tbody></table></div>';

        html += '<h3 style="font-size:14px;margin:14px 0 6px;">按会话统计</h3>';
        html += '<div class="dsh-tu-table-wrap"><table><thead><tr><th>会话 / 标题</th><th>工作区</th><th>模型</th><th>输入(未缓存)</th><th>缓存读取</th><th>缓存写入</th><th>输出</th><th class="dsh-tu-cost-col">估算费用</th></tr></thead><tbody>';
        d.rows.forEach(function (r) {
          var modelNames = (r.models || []).map(function (m) { return m.model; }).join(', ') || '—';
          html += '<tr><td>' + escapeHtml(r.title) + '</td><td class="dsh-tu-muted">' + escapeHtml(r.cwd) + '</td><td>' + escapeHtml(modelNames) + '</td><td>' + fmtInt(r.totals.input) + '</td><td>' + fmtInt(r.totals.cacheRead) + '</td><td>' + fmtInt(r.totals.cacheWrite) + '</td><td>' + fmtInt(r.totals.output) + '</td><td class="dsh-tu-cost-col">' + money(r.totals.cost) + '</td></tr>';
        });
        html += '</tbody></table></div>';
        panel.innerHTML = html;
      }

      function mountCard() {
        var btn = findSettingsButton();
        if (!btn) return false;
        var area = btn.closest('.hHd-Xa_settingsArea, [class*="settingsArea"], [class*="sidebar"]')
                   || btn.parentElement;
        if (!area || !area.parentElement) return false;
        if (!document.getElementById('dsh-tu-card')) {
          var card = buildCard();
          area.parentElement.insertBefore(card, area);
        }
        return true;
      }

      function scheduleMount() {
        var tries = 0;
        function tryMount() {
          if (mountCard()) return;
          if (tries++ < 120) setTimeout(tryMount, 250);
        }
        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', function () { setTimeout(tryMount, 300); });
        } else {
          tryMount();
        }
        // Guard against React re-render removing the card.
        var mo = new MutationObserver(function () {
          if (!document.getElementById('dsh-tu-card')) {
            if (mountCard()) renderCard();
          }
          scheduleSelectionCheck();
        });
        function scheduleSelectionCheck() {
          if (scheduleSelectionCheck._timer) return;
          scheduleSelectionCheck._timer = setTimeout(function () {
            scheduleSelectionCheck._timer = null;
            var sig = selectedSessionSignature();
            if (sig && sig !== scheduleSelectionCheck._last) {
              scheduleSelectionCheck._last = sig;
              refresh();
            }
          }, 500);
        }
        var rootObserve = function () {
          var root = document.getElementById('root') || document.body;
          mo.observe(root, { childList: true, subtree: true });
        };
        if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', rootObserve);
        else rootObserve();
      }

      function refresh() {
        loadList().then(function () {
          renderCard();
        }).catch(function () {
          renderCard();
        });
      }

      window.__dshTuSetCurrency = function (c) { setCurrency(c); };
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
          if (typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('\u5fc5\u987b\u662f JSON \u5bf9\u8c61');
          // Validate each entry
          Object.keys(parsed).forEach(function (k) {
            var v = parsed[k];
            if (typeof v === 'object' && v !== null) {
              if (v.peak && typeof v.peak === 'object') {
                // peak/off-peak format - ok
              } else if ('input' in v || 'output' in v) {
                // simple format - ok
              } else {
                throw new Error(k + ': \u65e0\u6548\u683c\u5f0f');
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
          if (errEl) { errEl.textContent = '\u683c\u5f0f\u9519\u8bef\uff1a' + e.message; errEl.style.display = 'block'; }
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
      };

      injectStyle();
      loadCustomPricing();
      loadPricing().then(function () {
        refresh();
        if (window.__dshTuRefreshTimer) clearInterval(window.__dshTuRefreshTimer);
        window.__dshTuRefreshTimer = setInterval(refresh, 30000);
      });
      scheduleMount();
    }

    exports.apply = apply;
    exports.inject = [];
    return module.exports;
  }
});
