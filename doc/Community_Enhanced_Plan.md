# 社区增强版（阶段2）实施方案

## 范围与原则

在现有社区 MVP（浏览 + 筛选 + 我也是）基础上，新增 4 个能力：
1. 用户贡献流程
2. AI 脱敏
3. 个性化推荐
4. 对话中案例引入（务实简化版）

**工程原则**：
- 沿用现有函数式 service 风格、`get_db()`、prompts/*.txt + templates.py 加载方式
- 不引入新依赖（不上向量库/embedding）
- 不阻塞主对话流程，新增 LLM 调用都放在用户主动触发的路径上

---

## 数据库改动（init_db 内，遵循 _migrate_add_column 约定）

### cards 表
- 新增 `shared_case_id INTEGER DEFAULT NULL` — 标记该卡片是否已分享到社区、对应案例 id，防重复分享

### decision_cases 表
- 新增 `source_card_id TEXT DEFAULT ''` — 来源卡片（运营预置为空）
- 新增 `is_user_contributed INTEGER DEFAULT 0` — 区分用户贡献 vs 预置

> 用 `_migrate_add_column` 增量加列，旧数据不受影响。

---

## 功能①+②：用户贡献 + AI 脱敏（一对组合）

### 流程
```
已关闭卡片详情页
  → 点"分享到社区"
  → 弹出复盘表单：满意度(1-10) + 一句话感受
  → 后端用 LLM 把【卡片信息+对话+复盘】脱敏成结构化案例（预览，未入库）
  → 前端展示可编辑预览
  → 用户确认 → 写入 decision_cases
```

### 后端
1. 新 prompt `case_desensitize.txt`：
   - 输入：卡片标题/核心矛盾/触发点/决策结果 + 对话摘要 + 用户复盘
   - 输出 JSON：`{title, background, core_conflict, final_choice, turning_point, tags}`
   - 强约束：**去除公司名、人名、具体薪资数字**，背景泛化为"互联网3年 | 薪资+30%"这种
2. `case_service.py` 新增：
   - `build_case_preview(card_id, retrospect_score, retrospect_text) -> dict`
     - 读 card + messages + user profile
     - 调 LLM 脱敏 → 合并 duration_days(由 created/closed 算) + decision_style/life_stage(取自 user)
     - 返回预览 dict（不入库）
   - `publish_case(card_id, case_data) -> int`
     - 写入 decision_cases，设 `is_user_contributed=1, source_card_id`
     - 回写 cards.shared_case_id 防重复
3. `card_router.py` 新增：
   - `POST /api/cards/{card_id}/share/preview` body: `{retrospect_score, retrospect_text}`
   - `POST /api/cards/{card_id}/share/confirm` body: `{case_data}`

### 前端（CardChat.jsx，status != active 区域）
- 已关闭卡片底部加"分享到社区"按钮（若 shared_case_id 已存在则显示"已分享"）
- 点击 → 复盘表单 modal → 调 preview → 可编辑预览 modal → confirm
- 成功后 toast 提示

---

## 功能③：个性化推荐（规则打分，不上向量）

### 打分逻辑（case_service.py 新增 `get_recommended_cases(uid, limit=3)`）
读 user profile，对每条未删除案例打分：
- case_type ∈ 用户 frequent_dilemma_types → +3
- decision_style 匹配 → +2
- life_stage 匹配 → +1
- tags 与用户价值观/关注领域有重叠 → 每个 +0.5
- 同分时 retrospect_score 高的优先

取 top N（默认3）。无 profile 时降级为"精选优先"。

### 后端
- `GET /api/cases/recommended?uid=xxx&limit=3`

### 前端（Community.jsx 顶部）
- "为你推荐"区块，展示 2-3 张推荐案例（复用现有案例卡片组件）
- 推荐区与下方"全部浏览"区视觉区分

---

## 功能④：对话中案例引入（务实简化版）

### 与原设计的差异（重要）
- ❌ 不做"每条消息跑 LLM 检测僵局"（延迟+成本+易误判）
- ✅ 用**启发式触发**：`stage == "advising"` 且能匹配到同类案例时
- ✅ 案例作为**独立"相似案例参考"卡片**返回，前端单独展示，**不塞进 AI 生成**

### 后端（chat_service.py 的 chat() 内）
1. 新增 `_find_related_case(card) -> dict | None`：
   - 按 card.dilemma_type 匹配 case_type
   - 在同类中按 core_conflict 关键词重叠选最相关一条
   - 排除用户自己刚分享的案例（source_card_id != card_id）
2. 在 chat() 返回里新增 `related_case` 字段：
   - 仅当 `stage == "advising"` 且找到匹配案例时返回
   - 每张卡片整个会话最多推一次（用一个轻量去重，比如查 messages 里是否已推过——简化为：只在首次进入 advising 时返回）

> 不改 system_prompt 生成逻辑，零风险污染主回复。

### 前端（CardChat.jsx）
- chat 响应带 `related_case` 时，在 AI 气泡下方渲染一张"💡 相似的人怎么选的"参考卡片
- 可展开看转折点+结果，可关闭

---

## 文件清单

### 后端
- `database.py` — 加 3 个列 + 对应迁移
- `prompts/case_desensitize.txt` — 新增脱敏 prompt
- `prompts/templates.py` — 注册新 prompt
- `services/case_service.py` — 加 `build_case_preview`/`publish_case`/`get_recommended_cases`/`_find_related_case`
- `routers/case_router.py` — 加 recommended 接口
- `routers/card_router.py` — 加 share/preview、share/confirm 接口
- `services/chat_service.py` — chat() 返回加 related_case

### 前端
- `api/index.js` — 加 4 个接口封装
- `pages/Community.jsx` — 顶部推荐区
- `pages/CardChat.jsx` — 分享按钮+复盘/预览 modal、相似案例参考卡片

---

## 实施顺序（每步独立可测）

1. **数据库改列**（10min，先跑通迁移）
2. **功能③推荐**（最简单、无 LLM、先建立信心）
3. **功能①+②贡献+脱敏**（核心，含 LLM 脱敏）
4. **功能④对话引入**（最后，触碰主对话流程，最谨慎）
5. **前端逐个对接 + 端到端测试**

---

## 风险与规避

| 风险 | 规避 |
|------|------|
| 脱敏不干净（漏了公司名） | prompt 强约束 + 用户可编辑预览再确认 |
| 推荐无 profile 时报错 | 降级为精选优先 |
| 对话引入变烦 | 仅 advising 阶段、每会话最多一次、独立卡片可关闭 |
| 循环 import | chat_service 单向 import case_service，无循环 |
| 重复分享同一卡片 | shared_case_id 防重 |
| LLM 脱敏失败 | try/except 降级：返回基于卡片字段的简单脱敏版 |

---

## 工作量预估
- 数据库 + 推荐：0.5 天
- 贡献 + 脱敏：1 天
- 对话引入：0.5 天
- 前端对接 + 测试：1 天
- **合计约 3 天**
