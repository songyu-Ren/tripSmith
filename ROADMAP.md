# ROADMAP

本路线图以“每天可交付的小步迭代”为原则，按优先级记录 Next 事项。

## Now（已具备）

- Trip / Constraints / Plan / Itinerary 端到端闭环（含导出）
- Saved Plans：保存方案并从保存方案生成行程
- Job：异步执行、进度/阶段、失败原因与 next action
- 统一错误响应：error_code + request_id（dev 下可带 details）
- 基础 UI：三页闭环（首页→结果→行程），包含错误卡片与重试

## Next（优先级）

### P0（稳定性与契约）

- packages/shared 作为单一真源：从 API OpenAPI 自动生成 types，并增加契约测试（OpenAPI 变更触发前端编译校验）
- Job 事件流标准化：阶段枚举统一、阶段到进度映射固定，并加入 request_id/trace_id 贯穿 worker 日志
- 错误码体系完善：将 Provider/LLM 错误映射为 PROVIDER.* / LLM.*，并加入可观测指标（失败率、耗时）

### P1（可用性与体验）

- 方案对比升级：评分卡可视化、差异高亮、维度一键切换
- 行程页可编辑：改时间/改 POI/删条目/重排，并保存（含回滚）
- Loading / Skeleton / Empty states 全覆盖，并梳理文案一致性

### P2（产品能力扩展）

- 地图体验：MapLibre + OSM（行程页展示 POI 标记与线路）
- 价格提醒引擎增强：去抖动、阈值类型（绝对/百分比）、频率控制
- 引入一个真实 Provider 参考实现（其余保持 stub + mock fallback）

