#!/usr/bin/env bash
# Uninstall @deepseek-ai/dsh-token-usage from the local DeepSeek Harness profile.
set -euo pipefail

DSH_HOME="${DSH_HOME:-$HOME/.dsh}"
PROFILE_NODE="$DSH_HOME/profiles/node_modules/@deepseek-ai"
PROFILE_PATCH="$DSH_HOME/profiles/web/cordis.patch.yml"

echo "==> 移除插件目录"
rm -rf "$PROFILE_NODE/dsh-token-usage"

if [ -f "$PROFILE_PATCH" ]; then
  echo "==> 从 profile patch 移除 token-usage 条目"
  # Remove the exact insert block if it was added by install.sh.
  python3 - "$PROFILE_PATCH" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8')
block = '\n- insert:\n    - id: token-usage\n      name: \'@deepseek-ai/dsh-token-usage\'\n'
if block in text:
    text = text.replace(block, '\n', 1)
    p.write_text(text, encoding='utf-8')
    print('   已移除')
else:
    print('   未发现 install.sh 写入的独立块，跳过')
PY
fi

echo "✅ 卸载完成。请重启 DeepSeek Harness 客户端以生效。"
