# Random Notes 部署说明

## 架构

| 服务 | 说明 |
|------|------|
| `db` | PostgreSQL 16，数据卷 `pgdata` |
| `api` | FastAPI + Uvicorn，端口容器内 `8000`（不直接暴露宿主机） |
| `web` | Nginx 托管前端静态资源，并把 `/<子路径>/api/` 反代到 `api:8000` |

构建上下文为**仓库根目录**（`docker-compose.yml` 在 `deploy/` 下，`context: ..`）。

## 环境要求

- Docker Engine、Docker Compose v2
- 服务器可访问镜像仓库（拉取 `postgres`、`python`、`node`、`nginx` 等）

## 首次部署

### 1. 获取代码

```bash
git clone <你的仓库地址> Random-Notes
cd Random-Notes
```

### 2. 配置环境变量

```bash
cd deploy
cp env.example .env
```

编辑 `deploy/.env`（**不要提交 `.env` 到 Git**）。关键项：

| 变量 | 说明 |
|------|------|
| `POSTGRES_PASSWORD` | 数据库密码，必填 |
| `DEPLOY_SUBPATH` | 浏览器路径前缀，不含首尾斜杠，如 `notes` → 访问 `http://域名/notes/` |
| `WEB_PORT` | 宿主机映射端口，默认 `8080` |
| `SECRET_KEY` | 至少 32 字符随机串，用于 JWT 等 |
| `COOKIE_PATH_PREFIX` | 与前端子路径一致，**带前导斜杠**，如 `/notes`（与 `DEPLOY_SUBPATH=notes` 对应） |
| `CORS_ALLOWED_ORIGINS` | 浏览器实际访问的**完整源**，逗号分隔，如 `https://example.com,https://www.example.com` |
| `PUBLIC_BASE_URL` | 站点对外的根 URL（含子路径），无尾部斜杠，如 `https://example.com/notes` |
| `APP_ENV` | 生产建议 `production`（关闭 OpenAPI 文档） |
| `ENFORCE_HTTPS` / `COOKIE_SECURE` | 全站 HTTPS 时：`ENFORCE_HTTPS=true`，`COOKIE_SECURE=true` |
| `REQUIRE_SMS_VERIFICATION` | 无短信网关时 `false`；此时注册需设置密码，登录用账号/手机号+密码 |
| `GLOBAL_API_RATE_LIMIT_*` / `REGISTER_RATE_LIMIT_*` | 应用层限流，见 `env.example` |
| `TRUSTED_HOSTS` | 可选；填写公网域名（逗号分隔）可限制 `Host` 头，防 Host 头攻击 |

`docker-compose.yml` 会向 `api` 注入 `DATABASE_URL` 与 `UPLOAD_DIR`，一般无需在 `.env` 里手写 `DATABASE_URL`。

### 3. 启动

```bash
cd deploy
docker compose up -d --build
```

### 4. 访问

- 仅本机 Docker： `http://127.0.0.1:<WEB_PORT>/<DEPLOY_SUBPATH>/`
- 前面还有一层 Nginx/反代时：通常把流量转到 `127.0.0.1:<WEB_PORT>`，并保证浏览器请求的 **Origin** 落在 `CORS_ALLOWED_ORIGINS` 中。

## 发版（代码已推送到远端）

在服务器仓库目录执行：

```bash
cd /path/to/Random-Notes
git pull
cd deploy
docker compose up -d --build
```

仅改后端或前端时可缩小重建范围：

```bash
docker compose up -d --build api
docker compose up -d --build web
```

## 数据库与迁移

应用启动时会执行 `create_db_and_tables()`，自动建表并做部分列的兼容补全。常规发版**不必**单独跑 Alembic；若你自行引入迁移脚本，再在 `api` 容器内按项目约定执行即可。

## 数据持久化

| 卷名 | 用途 |
|------|------|
| `pgdata` | PostgreSQL 数据 |
| `uploads` | 用户上传等媒体文件（挂载到 `api` 的 `/data/uploads`） |

停止服务但保留数据：

```bash
docker compose down
```

**删除卷会清空数据库与上传文件**（慎用）：

```bash
docker compose down -v
```

## 日志与排查

```bash
cd deploy
docker compose logs -f api
docker compose logs -f web
docker compose logs -f db
```

常见问题：

- **登录后立刻掉线 / Cookie 无效**：检查 `COOKIE_PATH_PREFIX` 是否与 `DEPLOY_SUBPATH` 一致、是否 HTTPS 与 `COOKIE_SECURE` 一致。
- **跨域错误**：把实际访问地址完整写进 `CORS_ALLOWED_ORIGINS`（含协议与端口）。
- **429 Too many requests**：适当调高 `GLOBAL_API_RATE_LIMIT_*`，或临时设为 `GLOBAL_API_RATE_LIMIT_MAX_REQUESTS=0` 关闭应用层全局限流（仍保留 Nginx `limit_req`）。

## 子路径与外层 Nginx

容器内 Nginx 已处理 `/<DEPLOY_SUBPATH>/` 与 `/<DEPLOY_SUBPATH>/api/`。外层反代示例思路：

- `location /notes/` → `proxy_pass http://127.0.0.1:8080/notes/`（端口与 `WEB_PORT` 一致）
- 保留或正确转发 `X-Forwarded-For`、`X-Forwarded-Proto`，以便限流与 HTTPS 判断。

## 安全建议

- 使用强 `SECRET_KEY`、`POSTGRES_PASSWORD`。
- 公网务必 HTTPS，并同步 `ENFORCE_HTTPS`、`COOKIE_SECURE`、`CORS_ALLOWED_ORIGINS`、`PUBLIC_BASE_URL`。
- 可配置 `TRUSTED_HOSTS` 为你的域名。
- 云厂商防火墙只开放必要端口，必要时在前缘启用 WAF。

## 相关文件

- `deploy/docker-compose.yml`：编排定义
- `deploy/env.example`：环境变量模板
- `docker/Dockerfile.api` / `docker/Dockerfile.web`：镜像构建
- `docker/nginx.subpath.template.conf` / `docker/nginx-limits.conf`：前端与反代、限流
