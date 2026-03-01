# EChin Assistant

Smart Assistant 后端 API（FastAPI + PostgreSQL）。

## 本地运行

### 1. 启动 Docker（数据库和 Redis）

后端依赖 PostgreSQL 和 Redis，用 Docker 跑：

```bash
# 在项目根目录 echin-assistant 下
docker compose up -d
```

**跑之前先确认 Docker 已启动**（Docker Desktop 或 Docker 引擎在运行）。  
检查容器是否起来：

```bash
docker compose ps
```

应看到 `smart_assistant_db`（5432）和 `smart_assistant_redis`（6379）为 running。

### 2. 配置环境变量

在 `backend` 目录下放一个 `.env` 文件，例如：

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/smart_assistant
JWT_SECRET=你的密钥随便写一段长字符串
JWT_ALG=HS256
```

（与 `docker-compose.yml` 里的 postgres 用户/密码/库名一致即可。）

### 3. 安装依赖并启动后端

**必须在 `backend` 目录下执行 uvicorn**（否则会报 `ModuleNotFoundError: No module named 'app'`）：

```bash
cd backend
python -m venv .venv          # 可选，建议用虚拟环境
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

- 默认地址：<http://127.0.0.1:8000>
- 接口文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>

---

## 常用命令备忘

| 想做的事           | 命令 |
|--------------------|------|
| 启动数据库/Redis   | `docker compose up -d` |
| 看容器状态         | `docker compose ps` |
| 停掉容器           | `docker compose down` |
| 启动后端           | `cd backend` → `uvicorn app.main:app --reload --port 8000` |

每次本地开发前：**先确认 Docker 已启动并 `docker compose up -d`，再在 `backend` 目录下跑 uvicorn。**

---

## 本地测试接口（不用记 token）

用 Swagger 测接口时，不必记旧 token，用固定测试账号随时重新拿即可。

### 推荐：固定测试账号 + Swagger Authorize

1. 用固定账号先 **signup 一次**（只需一次），例如：
   - Email: `test1@example.com`
   - Password: `123456`
2. 以后每次测试：
   - 打开 <http://127.0.0.1:8000/docs>
   - 调 **POST /auth/login**，用上面账号登录，拿到新 token
   - 点右上角 **Authorize**，把 token 粘进去
   - 之后所有需要登录的接口都会自动带 token

这样不用保存 token，每次都能重新生成，也符合真实流程（token 会过期）。

### 可选：清空数据库重新来

本地玩乱了想从头来时，可以删掉数据库数据（**会删掉所有数据**）：

```bash
docker compose down -v
docker compose up -d
```

`-v` 会删掉 postgres 的 volume，数据库全新；再启动后端即可。之后用同一组测试账号重新 signup 一次即可。
