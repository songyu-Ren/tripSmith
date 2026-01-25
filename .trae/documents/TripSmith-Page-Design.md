# TripSmith 页面设计说明（MVP，Desktop-first）

## Global Styles（全局）
- Design tokens
  - 背景：#0B1220（深色）/ #FFFFFF（浅色，默认可切换）
  - 主色：#4F46E5（强调按钮/链接）
  - 成功/警告/错误：#16A34A / #F59E0B / #DC2626
  - 边框/分割线：rgba(148,163,184,0.25)
  - 圆角：12px（卡片），8px（按钮/输入）
  - 阴影：card 0 10px 30px rgba(0,0,0,0.20)
- Typography
  - H1 28/36, H2 22/30, H3 18/26, Body 14/22, Caption 12/18
  - 数字与时间字段使用等宽字体（便于对齐）
- Button states
  - Primary：默认主色实心；hover 亮度 +6%；disabled 40% 不透明
  - Secondary：描边 + 透明底；hover 轻底色
- Link
  - 默认主色；hover 下划线；外链图标提示
- Layout system
  - 桌面：CSS Grid（12 列，max-width 1200px，左右 padding 24px）
  - 平板/移动：断点 1024/768/480，逐步收敛为单列堆叠；侧栏折叠为抽屉

---

## 1) 首页（旅行需求表单）
### Meta Information
- title: TripSmith | AI 行程规划
- description: 用可插拔 Provider 与 Agent 流程生成可执行行程
- og:title/og:description 同上；og:type=website

### Page Structure
- 顶部导航（通栏）+ 需求表单卡片（居中）+ 说明/示例 + 页脚

### Sections & Components
1. 顶部导航栏（Flex）
   - 左：Logo（TripSmith）
   - 右：状态区（当前 `user_id` 的简短展示 + “重置”）
2. 需求表单（Card）
   - origin（输入框）
   - destination（输入框）
   - dates（开始/结束日期）
   - flexible dates（数字输入：±天）
   - budget（总预算 + currency）
   - travelers（数字输入）
   - preferences（多选/标签：节奏、饮食、亲子、夜生活、步行偏好等）
   - CTA：生成方案（创建 Trip 并跳转结果页）
3. 说明区
   - 提示 Mock 模式可离线跑通；真实 Provider 需要配置 key（在 `.env`）
4. 页脚
   - 文案 + GitHub 链接

---

## 2) 结果页（展示 3 套方案）
### Meta Information
- title: TripSmith | 行程编辑
- description: 编辑约束与偏好，触发 Agent 生成并迭代
- og:type=article（分享页用）

### Page Structure
- 顶部返回 + Trip 摘要 + 三套方案卡片（Stack）

### Sections & Components
1. Trip 摘要
   - origin/destination、日期、预算、人数、偏好标签
   - 操作：重新生成方案
2. 方案卡片（至少 3 张）
   - 标题：省钱 / 省时间 / 平衡
   - 航班摘要：出发/到达、转机次数、时长、价格
   - 住宿摘要：位置、每晚、总价
   - 指标：总价、总时长、转机次数、每日通勤时间估计
   - 解释：评分与原因（cost_score/time_score/comfort_score）
   - CTA：生成详细行程（进入行程页）
   - 次 CTA：订阅价格提醒（modal：type/threshold/frequency）
3. 导出
   - 链接按钮：导出 ICS / 导出 Markdown

### Responsive
- <=1024：侧栏折叠为抽屉；双栏变单栏，上预览下编辑可切换 Tabs

---

## 3) 行程页（逐日 itinerary）
### Meta Information
- title: TripSmith | 设置
- description: 管理 Provider 连接与默认偏好

### Page Structure
- 顶部返回 + 方案摘要 + 逐日折叠面板（Day 1..n）

### Sections & Components
1. 逐日列表
   - 每天 3 个时段：上午/下午/晚上
   - 每条包含：POI 名称、预计停留时间、通勤方式与时长、天气摘要
2. 错误与冲突
   - 若生成失败，展示后端 error message 与重试按钮
3. 导出
   - 同结果页：ICS/Markdown

---

## 4) 通用状态与组件
- GlobalToast：用于成功/错误提示。
- LoadingSkeleton：用于 plan/itinerary 生成等待。
- ErrorCard：用于 API 错误（含请求 id 与重试）。
