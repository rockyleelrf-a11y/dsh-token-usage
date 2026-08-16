#!/usr/bin/env bash
# One-click installer for @deepseek-ai/dsh-token-usage
#
# Installs the Token Usage & Cost dashboard into the local DeepSeek Harness
# web profile, so it appears in Settings -> Plugin Inventory and shows a card
# above Settings in the sidebar.
set -euo pipefail

PLUGIN_NAME="@deepseek-ai/dsh-token-usage"
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
mkdir -p "$PROFILE_NODE"
rm -rf "$PROFILE_NODE/dsh-token-usage"
cp -R "$PLUGIN_SRC/package.json" "$PROFILE_NODE/dsh-token-usage/"
mkdir -p "$PROFILE_NODE/dsh-token-usage/lib"
cp "$PLUGIN_SRC/lib/index.js" "$PROFILE_NODE/dsh-token-usage/lib/index.js"
cp "$PLUGIN_SRC/lib/client.js" "$PROFILE_NODE/dsh-token-usage/lib/client.js"

echo "==> 写入 profile patch"
if [ ! -f "$PROFILE_PATCH" ]; then
  mkdir -p "$(dirname "$PROFILE_PATCH")"
  printf '%s\n' "# dsh profile root — an empty entry list." "[]" > "$PROFILE_PATCH"
fi

if ! grep -q "dsh-token-usage" "$PROFILE_PATCH"; then
  cat >> "$PROFILE_PATCH" <<'PATCH'

- insert:
    - id: token-usage
      name: '@deepseek-ai/dsh-token-usage'
PATCH
  echo "   已追加 token-usage 到 $PROFILE_PATCH"
else
  echo "   token-usage 已存在于 $PROFILE_PATCH，跳过"
fi

echo "✅ 安装完成。请重启 DeepSeek Harness 客户端（或刷新 Web 界面）以加载插件。"
echo ""
echo "   验证：打开 设置 -> 插件列表，应能看到 dsh-token-usage。"
