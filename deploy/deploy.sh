#!/usr/bin/env bash
set -euo pipefail
# 用法：在 Ubuntu 上于仓库根目录执行，或先 rsync 同步代码再执行。
# 依赖：docker.io、docker compose 插件、仓库内 deploy/.env 已配置。

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/deploy"

test -f .env || { echo "缺少 deploy/.env，从 env.example 复制"; exit 1; }

docker compose build --pull
docker compose up -d

echo "本机验证: http://127.0.0.1:8080/notes/ （端口与 DEPLOY_SUBPATH 以 .env 为准）"
echo "宿主机 Nginx 反代见 deploy/host-nginx-snippet.conf"
