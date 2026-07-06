#!/bin/bash
# 三备份空间同步脚本
# 用途：将 GitHub 主仓库同步到 GitLab 和 Gitee 作为备份
#
# 使用方法：
#   chmod +x scripts/backup.sh
#   ./scripts/backup.sh
#
# 前置条件（首次运行需配置）：
#   git remote add gitlab <你的 GitLab SSH/HTTPS URL>
#   git remote add gitee  <你的 Gitee SSH/HTTPS URL>
#
# 之后每次运行自动 push 到三个仓库

set -euo pipefail

echo "=== 价格观察站 · 三备份同步 ==="
date

cd "$(dirname "$0")/.."
ROOT=$(pwd)

echo "[1/3] 同步主仓库 (GitHub) ..."
git add -A
git commit --allow-empty -m "auto-sync: $(date '+%Y-%m-%d %H:%M')" || true
git push origin main 2>&1 | tail -3

for REMOTE in gitlab gitee; do
    if git remote get-url "$REMOTE" >/dev/null 2>&1; then
        echo "[$(expr $REMOTE + 1)/3] 推送 $REMOTE ..."
        git push "$REMOTE" main 2>&1 | tail -3
    else
        echo "[!] $REMOTE 未配置，跳过"
    fi
done

echo "=== 备份同步完成 $(date) ==="
