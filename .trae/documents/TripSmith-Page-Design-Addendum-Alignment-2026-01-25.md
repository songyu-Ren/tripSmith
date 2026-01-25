# TripSmith 页面设计说明（对齐增补，Desktop-first）

## Global Styles（全局）
- Layout
  - 桌面优先：12 列 CSS Grid（max-width 1200px，gutter 24px），主体内容居中。
  - 响应式断点：1024/768/480；表格与卡片在 <=768 自动单列堆叠。
- 颜色与层级
  - 背景：#0B1220（深色基底）
  - 主色：#4F46E5（按钮/链接/高亮）
  - 边框：rgba(148,163,184,0.25)，卡片阴影 0 10px 30px rgba(0,0,0,0.20)
- 字体
  - H1 28/36，H2 22/30，H3 18/26，Body 14/22，Caption 12/18
  - 时间/金额字段使用等宽字体以便对齐
- 交互状态
  - Primary 按钮：hover 亮度 +6%；disabled 40% 不透明
  - Link：hover 下划线；外链带 icon

---

## 1) 首页（旅行需求表单）
### Meta Information
- title: TripSmith | 旅行方案生成
- description: 输入出行条件，生成 3 套可解释旅行方案
- og:title/og:description 同上；og:type=website

### Page Structure
- 顶部导航（通栏） + 主表单卡片（居中） + 示例说明（两列信息区） + 页脚

### Sections & Components
1. 顶部导航栏（Flex，左右对齐）
   - 左：Logo（TripSmith）
   - 右：会话区（匿名 user_id 简短展示）+ “重置会话”按钮
2. 需求表单（Card，Grid）
   - 两列布局：左列地点与日期，右列预算/人数/偏好；<=768 变单列
   - 字段：origin、destination、start/end date、flexible days、budget+currency、travelers、preferences（Tag 多选）
   - 校验：必填提示/日期范围错误提示（就地提示 + 顶部汇总提示）
   - CTA：生成方案（创建 Trip 后跳转结果页）
3. 示例说明（Info Panel）
   - 说明“mock 可跑通；接入真实 LLM/Provider 为可选项”

---

## 2) 方案结果页（展示 3 套方案）
### Meta Information
- title: TripSmith | 方案结果
- description: 查看 3 套方案，选择生成逐日行程，并支持导出与提醒订阅
- og:type=website

### Page Structure
- 顶部返回 + Trip 摘要条 + 方案卡片列表（纵向 Stack） + 页面底部导出区

### Sections & Components
1. Trip 摘要条（Sticky optional）
   - 展示：地点/日期/预算/人数/偏好标签
   - 操作：重新生成方案（secondary）
2. 方案卡片（3 张固定）
   - Header：省钱/省时间/平衡 + 关键指标 chips（总价/总时长/转机/舒适度）
   - Body：摘要（3-6 行）+ “为什么是这个方案”（可折叠）
   - Actions：
     - Primary：生成详细行程（进入行程页）
     - Secondary：订阅价格提醒（弹窗表单：type/threshold/frequency）
3. 导出区（Card 或 Inline）
   - 按钮：导出 ICS、导出 Markdown（下载/新窗口预览均可）
4. 状态组件
   - Plan 生成 LoadingSkeleton；ErrorCard（错误文案 + 重试）

---

## 3) 行程页（逐日 itinerary）
### Meta Information
- title: TripSmith | 逐日行程
- description: 查看并生成逐日行程（上午/下午/晚上），支持导出
- og:type=website

### Page Structure
- 顶部返回 + 选中方案摘要 + 逐日折叠面板（Day 1..n）+ 导出区

### Sections & Components
1. 方案摘要（Compact Card）
   - 展示所选方案标题与关键指标
   - 操作：重新生成行程（secondary）
2. 逐日行程（Accordion）
   - 每天包含 3 个时段：上午/下午/晚上（Timeline 风格）
   - 单条活动：POI 名称、预计停留时间、通勤方式与时长、天气摘要（如无则显示“暂无/Mock”）
3. 异常与冲突（Inline Notice）
   - 生成失败：展示错误原因 + 重试按钮；保留上次成功内容
4. 导出区
   - 同结果页：ICS/Markdown

---

## 对齐修正摘要（便于你合并）
- 修正“行程页 Meta/文案”不一致：不再出现“设置/Provider 连接”等描述，统一为 itinerary。
- 统一导出交互：导出不是独立页面，而是结果页/行程页的通用模块。
- 统一信息架构：三页闭环（首页→结果→行程），所有核心功能均从首页可达。