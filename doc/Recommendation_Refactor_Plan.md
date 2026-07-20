# 推荐功能重构：从"画像驱动"改为"纠结驱动"

## 问题诊断

**现状（错的）**：用户一注册、还没任何纠结卡片时，社区页顶部就根据画像推了一堆案例。
- 画像驱动 = "猜你喜欢"，但用户来社区不是逛兴趣，是找"跟我这个纠结相似的人怎么选的"
- 没有具体纠结时推荐，等于无的放矢

**目标（对的）**：推荐从**用户的具体纠结**出发，画像只做辅助加权。
- 必须先有纠结卡片（聊过 or 已关闭）才触发
- 用卡片的核心矛盾/关注点去匹配相似案例

---

## 方案

### 决策
- **入口**：卡片详情页内推荐（社区页去掉"为你推荐"区，回归纯浏览）
- **匹配**：结构化字段为主（dilemma_type + core_conflict + main_concern），卡片还没 core_conflict 时用 LLM 兜底提取

---

## 后端改动

### 1. case_service.py

**新增 `get_recommendations_for_card(card_id, limit=3)`**：纠结驱动的核心
```
输入：card_id
1. 读卡片（dilemma_type / core_conflict / title / main_concern）
2. 读卡片所属用户画像（decision_style / life_stage / values）作辅助
3. 同 case_type 候选集（排除用户自己分享的）
4. 打分 = 纠结关键词重叠(主, 权重高) + 画像加权(辅, 权重低)
   - core_conflict/main_concern/title 关键词重叠：每个 +2（主导）
   - decision_style 匹配：+1（辅助）
   - life_stage 匹配：+0.5（辅助）
   - 满意度作为同分 tie-breaker
5. core_conflict 为空时（卡片刚建还没聊）→ 用 LLM 从对话提取一个临时矛盾关键词再匹配；
   对话也很少时 → 降级用 dilemma_type + title 匹配
6. 返回 top N
```

**删除 `get_recommended_cases(uid)`**（画像驱动的旧函数）

**复用**：`_tokens()` 关键词切分、`find_related_case` 的匹配思路（两者逻辑合并/共享）

### 2. case_router.py
- 删除 `GET /api/cases/recommended?uid=`（画像驱动）
- 新增 `GET /api/cases/recommendations?card_id=xxx&limit=3`（纠结驱动）

---

## 前端改动

### 1. Community.jsx（社区页）
- **删除**"为你推荐"区块和 `getRecommendedCases` 调用
- 回归纯浏览：分类筛选 + 案例列表（保持现有）

### 2. CardChat.jsx（卡片详情页）
- 在卡片详情页加一个**"看看相似的人怎么选的"区块**：
  - 位置：对话区下方 / 或顶部卡片信息附近（折叠式，不打扰对话）
  - 触发条件：卡片有 core_conflict（已聊出眉目）或已关闭
  - 点击展开 → 调 `recommendations?card_id=` → 展示 2-3 张相似案例
  - 复用社区页的案例卡片样式
- 与功能④（对话中 advising 自动弹一条）的区别：
  - 功能④是 AI 主动在对话流里塞一条
  - 这个是用户主动点"看相似案例"，可看多条

### 3. api/index.js
- 删除 `getRecommendedCases`
- 新增 `getCardRecommendations(cardId, limit)`

---

## 匹配打分细节（结构化为主 + LLM 兜底）

```python
def get_recommendations_for_card(card_id, limit=3):
    card = 读卡片
    if not card or not card.dilemma_type:
        return []

    # 纠结关键词（主导）——结构化字段优先
    conflict_text = card.core_conflict
    if not conflict_text:
        # 兜底：卡片还没聊出核心矛盾，用 LLM 从对话提取
        conflict_text = _extract_conflict_via_llm(card_id)  # 失败则用 title
        if not conflict_text:
            conflict_text = card.title or ""

    card_tokens = _tokens(conflict_text) | _tokens(card.main_concern) | _tokens(card.title)

    user = 读画像（辅助）
    候选 = 同 case_type 且 source_card_id != card_id

    def score(c):
        s = 2 * len(card_tokens & _tokens(c.core_conflict))   # 纠结匹配（主）
        s += 2 * len(card_tokens & _tokens(c.tags))           # 标签也算纠结匹配
        if user and c.decision_style in user.styles: s += 1   # 画像（辅）
        if user and c.life_stage == user.life_stage: s += 0.5 # 画像（辅）
        return s

    按 (score, retrospect_score) 降序，取 top N
```

**LLM 兜底只在 core_conflict 为空时触发**（一般卡片聊过 2-3 轮就有 core_conflict 了，所以兜底很少跑，成本可控）。

---

## 涉及文件
- `backend/services/case_service.py` — 删旧函数、加 `get_recommendations_for_card` + `_extract_conflict_via_llm`
- `backend/routers/case_router.py` — 换接口
- `frontend/src/api/index.js` — 换接口封装
- `frontend/src/pages/Community.jsx` — 删推荐区
- `frontend/src/pages/CardChat.jsx` — 加"看相似案例"区块

---

## 工作量：约 1.5 小时
