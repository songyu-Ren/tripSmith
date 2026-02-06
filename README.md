# TripSmith

TripSmith 是一个开源旅行规划 Copilot：输入出行条件与偏好，生成 3 套可解释方案（省钱/省时间/平衡），并可生成逐日行程与导出（ICS / Markdown）。

## 功能概览

- Trip 创建：地点/日期/预算/人数/偏好
- 约束生成与确认：先生成可解释约束，再确认后生成方案
- 方案生成（异步 Job）：返回进度、阶段与 request_id
- 行程生成（异步 Job）：按日展示并按 上午/下午/晚上 分段
- Saved Plans：可保存方案并从已保存方案生成行程
- 导出：ICS 日历、Markdown 行程
- 价格提醒（MVP）：mock 价格 + 定时检查 + 通知占位

## 本地运行（Docker Compose）

1. 启动服务：

   ```bash
   docker compose up --build
   ```

2. 打开：
   - Web：http://localhost:3000
   - API Docs：http://localhost:8000/docs

默认 Provider/LLM 为 mock（无需任何 Key 即可跑通）。如需接入真实 Provider，可在根目录复制 `.env.example` 为 `.env` 并填写相应 Key。

## 本地运行（不使用 Docker）

### API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Windows 请使用 .venv\Scripts\activate
pip install -r requirements.txt
uvicorn tripsmith.main:app --reload --port 8000
```

### Web

```bash
cd apps/web
npm install
npm run dev
```

## 测试与质量检查

### 后端

```bash
cd apps/api
pytest
ruff check .
```

### 前端

```bash
cd apps/web
npm run typecheck
npm run lint
npm run build
```

## Smoke Test

仓库包含一个端到端 smoke test（会 `docker compose up -d`，并通过 API 生成 trip/plan/itinerary 后校验 ICS）。

```bash
./scripts/smoke_test.sh
```

## 手动验证（3–6 步）

1. 首页填写出行条件 → 点击“生成方案”
2. 在结果页点击“生成约束”→ 微调后点击“确认约束并继续”
3. 点击“重新生成方案”，观察 Job 进度与阶段变化
4. 在任一方案卡片点击“保存此方案”，在“已保存的方案”区看到新增条目
5. 点击“生成行程”，在行程页按天查看并按 上午/下午/晚上 折叠分段
6. 点击“导出 ICS / 导出 Markdown”验证导出内容

