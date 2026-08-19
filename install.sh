#!/usr/bin/env bash
# One-click installer for @deepseek-ai/dsh-token-usage
#
# Installs the Token Usage & Cost dashboard into the local DeepSeek Harness
# web profile, so it appears in Settings -> Plugin Inventory and shows a card
# above Settings in the sidebar.
set -euo pipefail

PLUGIN_NAME="@deepseek-ai/dsh-token-usage"
PLUGIN_DIR_NAME="dsh-token-usage"
PLUGIN_SRC="$(cd "$(dirname "$0")" && pwd)"
DSH_HOME="${DSH_HOME:-$HOME/.dsh}"
PROFILE_NODE="$DSH_HOME/profiles/node_modules/@deepseek-ai"
PROFILE_PATCH="$DSH_HOME/profiles/web/cordis.patch.yml"

if [ ! -d "$DSH_HOME/profiles" ]; then
  echo "❌ 未找到 DSH profile 目录: $DSH_HOME/profiles"
  echo "   请先运行一次 DeepSeek Harness 客户端后再执行安装。"
  exit 1
fi

echo "==> 安装插件目录"
mkdir -p "$PROFILE_NODE/$PLUGIN_DIR_NAME/lib"
rm -rf "$PROFILE_NODE/$PLUGIN_DIR_NAME/lib"/*
cp "$PLUGIN_SRC/package.json" "$PROFILE_NODE/$PLUGIN_DIR_NAME/package.json"
cp "$PLUGIN_SRC/lib/index.js" "$PROFILE_NODE/$PLUGIN_DIR_NAME/lib/index.js"
cp "$PLUGIN_SRC/lib/client.js" "$PROFILE_NODE/$PLUGIN_DIR_NAME/lib/client.js"
cp "$PLUGIN_SRC/lib/pricing.json" "$PROFILE_NODE/$PLUGIN_DIR_NAME/lib/pricing.json" 2>/dev/null || true
cp "$PLUGIN_SRC/lib/pricing.js" "$PROFILE_NODE/$PLUGIN_DIR_NAME/lib/pricing.js" 2>/dev/null || true
echo "   已复制到 $PROFILE_NODE/$PLUGIN_DIR_NAME/"

echo "==> 写入 profile patch"
mkdir -p "$(dirname "$PROFILE_PATCH")"

if [ -f "$PROFILE_PATCH" ] && grep -q "dsh-token-usage" "$PROFILE_PATCH"; then
  echo "   token-usage 已存在于 $PROFILE_PATCH，跳过"
else
  # Handle the case where the file is empty or contains just "[]"
  if [ ! -f "$PROFILE_PATCH" ]; then
    # File doesn't exist yet — create it from scratch
    cat > "$PROFILE_PATCH" <<'PATCH'
# Token usage plugin patch

- insert:
    - id: token-usage
      name: '@deepseek-ai/dsh-token-usage'
PATCH
    echo "   已创建 $PROFILE_PATCH 并添加 token-usage"
  elif grep -q '^\[\]$' "$PROFILE_PATCH" 2>/dev/null; then
    # Empty template — replace the whole file
    cat > "$PROFILE_PATCH" <<'PATCH'
# Token usage plugin patch

- insert:
    - id: token-usage
      name: '@deepseek-ai/dsh-token-usage'
PATCH
    echo "   已替换空模板并添加 token-usage 到 $PROFILE_PATCH"
  else
    # Already has content — append cleanly
    cat >> "$PROFILE_PATCH" <<'PATCH'

- insert:
    - id: token-usage
      name: '@deepseek-ai/dsh-token-usage'
PATCH
    echo "   已追加 token-usage 到 $PROFILE_PATCH"
  fi
fi

echo "✅ 安装完成。请重启 DeepSeek Harness 客户端（或刷新 Web 界面）以加载插件。"
echo ""
echo "   验证：打开 设置 -> 插件列表，应能看到 dsh-token-usage。"
