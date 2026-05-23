#!/usr/bin/env bash
set -euo pipefail

SQL_FILE="${1:-/tmp/poetize.sql}"
NEW_PASSWORD="${2:-}"
API_CONTAINER="${API_CONTAINER:-deploy-api-1}"
MYSQL_CONTAINER="${MYSQL_CONTAINER:-poetize-mysql-import}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-tmp_poetize_import}"
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"

usage() {
  echo "用法: $0 [poetize.sql路径] <登录密码>"
  echo "示例: $0 /tmp/poetize.sql 'MyPass123!'"
  exit 1
}

[[ -n "$NEW_PASSWORD" ]] || usage
[[ -f "$SQL_FILE" ]] || { echo "找不到 SQL 文件: $SQL_FILE"; exit 1; }
[[ -f "$REPO_DIR/scripts/import_poetize.py" ]] || { echo "找不到 $REPO_DIR/scripts/import_poetize.py，请先 git pull"; exit 1; }
docker inspect "$API_CONTAINER" >/dev/null 2>&1 || { echo "找不到容器 $API_CONTAINER"; exit 1; }

NETWORK="$(docker inspect "$API_CONTAINER" --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{"\n"}}{{end}}' | head -n1)"
[[ -n "$NETWORK" ]] || { echo "无法获取 Docker 网络"; exit 1; }

echo "==> 网络: $NETWORK"
echo "==> 清理旧临时 MySQL"
docker rm -f "$MYSQL_CONTAINER" >/dev/null 2>&1 || true

echo "==> 启动临时 MySQL"
docker run -d --name "$MYSQL_CONTAINER" --network "$NETWORK" \
  -e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
  -e MYSQL_DATABASE=poetize \
  mysql:5.7 >/dev/null

cleanup() {
  docker rm -f "$MYSQL_CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> 等待 MySQL 就绪"
for _ in $(seq 1 60); do
  if docker exec "$MYSQL_CONTAINER" mysqladmin ping -uroot -p"$MYSQL_ROOT_PASSWORD" --silent 2>/dev/null; then
    break
  fi
  sleep 2
done
docker exec "$MYSQL_CONTAINER" mysqladmin ping -uroot -p"$MYSQL_ROOT_PASSWORD" --silent

echo "==> 导入 poetize.sql（可能需几分钟）"
docker exec -i "$MYSQL_CONTAINER" mysql -uroot -p"$MYSQL_ROOT_PASSWORD" poetize < "$SQL_FILE"

echo "==> 复制迁移脚本到 api 容器"
docker exec "$API_CONTAINER" mkdir -p /app/scripts
docker cp "$REPO_DIR/scripts/import_poetize.py" "$API_CONTAINER:/app/scripts/import_poetize.py"

echo "==> 安装 pymysql"
docker exec "$API_CONTAINER" pip install -q pymysql

echo "==> 执行迁移"
docker exec \
  -e POETIZE_MYSQL_URL="mysql+pymysql://root:${MYSQL_ROOT_PASSWORD}@${MYSQL_CONTAINER}:3306/poetize" \
  "$API_CONTAINER" \
  python /app/scripts/import_poetize.py --default-password "$NEW_PASSWORD"

echo ""
echo "导入完成。"
echo "登录用户名: hck"
echo "登录密码: $NEW_PASSWORD"
