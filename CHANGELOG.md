# CHANGELOG

## v0.2.1 (2026-02-06)

### Added

- Job 阶段字段（stage）与失败辅助信息（error_code / error_message / next_action）
- 前端统一 Job 轮询 hook，并在结果页与行程页复用
- 行程页按 上午/下午/晚上 分段折叠（Accordion）
- 错误卡片支持复制详情（dev 下展示 details）

### Changed

- error_code 分层：VALIDATION / RATE_LIMIT / JOB / INTERNAL（统一格式）
- UI 轻量设计 tokens（背景/边框/按钮/输入/卡片阴影）并统一应用到核心页面

### Fixed

- API client 在 body 无 JSON 时仍可从响应头获取 request_id

