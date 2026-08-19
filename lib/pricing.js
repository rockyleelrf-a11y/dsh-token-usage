// Pricing data module
// Loads pricing from the static JSON file (lib/pricing.json)
// Provides a fallback for the two DeepSeek models when JSON is unavailable.

export const FALLBACK_PRICING = {
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

export async function loadPricing() {
  try {
    const response = await fetch('/assets/token-usage-pricing.json');
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const data = await response.json();
    if (data && data.providerModel) {
      return data;
    }
  } catch (e) {
    // Fallback to static JSON file
  }
  try {
    const response = await fetch('lib/pricing.json');
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const data = await response.json();
    if (data && data.providerModel) {
      return data;
    }
  } catch (e) {
    // Final fallback
  }
  return FALLBACK_PRICING;
}
