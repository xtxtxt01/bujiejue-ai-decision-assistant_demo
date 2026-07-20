# API 完整文档

## 目录
- [认证 API](#认证-api)
- [用户 API](#用户-api)
- [卡片（纠结）API](#卡片纠结-api)
- [记忆 API](#记忆-api)
- [社区案例 API](#社区案例-api)

---

## 认证 API

### POST `/api/auth/register`
用户注册

**请求体：**
```json
{
  "username": "user123",
  "password": "secure_password",
  "nickname": "张三",
  "mbti": "INTP",
  "decision_style": "rational",
  "maximizer_tendency": "maximizer",
  "values_ranking": ["成长", "自由", "稳定"],
  "life_stage": "early_career",
  "frequent_dilemma_types": ["career", "growth"],
  "self_intro": "我是一名产品经理，常纠结于职业发展方向",
  "theme": "default"
}
```

**响应：**
```json
{
  "uid": "a1b2c3d4",
  "username": "user123",
  "nickname": "张三"
}
```

---

### POST `/api/auth/login`
用户登录

**请求体：**
```json
{
  "username": "user123",
  "password": "secure_password"
}
```

**响应：**
```json
{
  "uid": "a1b2c3d4",
  "username": "user123",
  "nickname": "张三",
  "theme": "default"
}
```

---

## 用户 API

### GET `/api/user/{uid}/profile`
获取用户画像

**响应：**
```json
{
  "uid": "a1b2c3d4",
  "username": "user123",
  "nickname": "张三",
  "mbti": "INTP",
  "decision_style": "rational",
  "maximizer_tendency": "maximizer",
  "values_ranking": "成长>自由>稳定",
  "life_stage": "early_career",
  "frequent_dilemma_types": "career,growth",
  "self_intro": "我是一名产品经理...",
  "theme": "default",
  "created_at": "2024-06-15T10:00:00",
  "updated_at": "2024-06-15T10:00:00"
}
```

---

### PUT `/api/user/{uid}/profile`
更新用户画像（部分更新）

**请求体：**
```json
{
  "mbti": "ENFJ",
  "decision_style": "intuitive",
  "values_ranking": ["自由", "成长", "稳定"]
}
```

**响应：**
```json
{
  "message": "更新成功"
}
```

---

## 卡片（纠结）API

### POST `/api/cards`
创建新的纠结卡片（自动触发首轮对话）

**请求体：**
```json
{
  "uid": "a1b2c3d4",
  "dilemma_type": "career",
  "initial_input": "我最近收到一个新 offer，不知道要不要跳槽",
  "trigger_event": "上周开完会觉得没成长空间",
  "feared_outcome": "担心新公司不适应，又浪费了现在的积累"
}
```

**响应：**
```json
{
  "card_id": "e5f6g7h8",
  "assistant_message": "嗯，我能感受到你的纠结...",
  "progress_hint": {
    "label": "初步了解你的情况",
    "tendency": null,
    "next_question": "能先聊聊现在公司的情况吗？"
  },
  "stage": "clarifying"
}
```

---

### GET `/api/cards?uid={uid}`
获取用户所有卡片列表

**响应：**
```json
{
  "cards": [
    {
      "id": "e5f6g7h8",
      "uid": "a1b2c3d4",
      "title": "跳槽 vs 留下",
      "dilemma_type": "career",
      "core_conflict": "成长机会 vs 稳定积累",
      "trigger_event": "上周开完会...",
      "main_concern": "担心新公司...",
      "status": "active",
      "created_at": "2024-06-16T09:00:00",
      "updated_at": "2024-06-16T15:30:00",
      "closed_at": null,
      "insight": null,
      "current_tendency": "{\"option_a\": 60, \"option_b\": 40, \"options\": [\"跳槽\", \"留下\"]}"
    }
  ]
}
```

---

### GET `/api/cards/{card_id}`
获取卡片详情及所有对话消息

**响应：**
```json
{
  "card": {
    "id": "e5f6g7h8",
    "uid": "a1b2c3d4",
    "title": "跳槽 vs 留下",
    "dilemma_type": "career",
    "core_conflict": "成长机会 vs 稳定积累",
    "status": "active",
    "current_tendency": "{\"option_a\": 60, \"option_b\": 40, \"options\": [\"跳槽\", \"留下\"]}",
    "insight": null
  },
  "messages": [
    {
      "id": "msg1",
      "card_id": "e5f6g7h8",
      "role": "user",
      "content": "我收到新 offer 了...",
      "created_at": "2024-06-16T09:00:00"
    },
    {
      "id": "msg2",
      "card_id": "e5f6g7h8",
      "role": "assistant",
      "content": "嗯，我能感受到你的纠结...",
      "created_at": "2024-06-16T09:00:15"
    }
  ]
}
```

---

### POST `/api/cards/{card_id}/chat`
在卡片内继续对话

**请求体：**
```json
{
  "uid": "a1b2c3d4",
  "message": "现在公司工作三年了，感觉学不到新东西"
}
```

**响应：**
```json
{
  "assistant_message": "三年确实是个坎儿...",
  "progress_hint": {
    "label": "你倾向于跳槽，但对稳定也有顾虑",
    "tendency": {
      "option_a": 60,
      "option_b": 40,
      "options": ["跳槽", "留下"]
    },
    "next_question": "新 offer 的具体情况是什么？"
  },
  "stage": "exploring",
  "card_updated": false,
  "card_info": null,
  "card_closed": false,
  "value_conflict_hint": null,
  "related_case": {
    "id": 12,
    "case_type": "career",
    "title": "三年产品经理的跳槽纠结",
    "core_conflict": "成长空间 vs 团队氛围",
    "final_choice": "最终选择了跳槽",
    "retrospect_score": 8
  }
}
```

**响应字段说明：**
- `progress_hint.tendency`：当前倾向百分比（`option_a` + `option_b` = 100）
- `card_updated`：是否提取并更新了卡片结构化信息
- `card_closed`：是否自动检测到决定并关闭了卡片
- `value_conflict_hint`：价值观冲突提示（第 5/10/15... 轮检测）
- `related_case`：相似社区案例（进入 advising 阶段时推荐一次）

---

### PUT `/api/cards/{card_id}/close`
手动关闭卡片（已决定 / 搁置）

**请求体：**
```json
{
  "uid": "a1b2c3d4",
  "status": "decided",  // decided | shelved
  "decision_result": "我决定接受新 offer",
  "decision_reason": "成长机会更重要"
}
```

**响应：**
```json
{
  "message": "卡片已关闭"
}
```

**说明：**
- 关闭后会触发后台任务生成 Insight
- 关闭时会全量提取对话记忆到 Memosyne

---

### PUT `/api/cards/{card_id}/reopen`
重新打开已关闭的卡片

**响应：**
```json
{
  "message": "卡片已重新打开"
}
```

---

### GET `/api/cards/insights?uid={uid}`
获取用户所有已生成 Insight 的卡片（Insight Gallery）

**响应：**
```json
{
  "insights": [
    {
      "id": "e5f6g7h8",
      "title": "跳槽 vs 留下",
      "dilemma_type": "career",
      "status": "decided",
      "insight": {
        "core_conflict": "成长机会 vs 稳定积累",
        "value_signals": ["成长>稳定", "长期>短期"],
        "worry_type": "损失厌恶型（怕失去当前积累）",
        "action_suggestion": "可以给自己设置 3 个月试错期..."
      },
      "created_at": "2024-06-16T09:00:00",
      "closed_at": "2024-06-16T18:00:00",
      "duration_days": 1
    }
  ]
}
```

---

### POST `/api/cards/{card_id}/share/preview`
生成脱敏后的社区案例预览（不入库）

**请求体：**
```json
{
  "retrospect_score": 8,
  "retrospect_text": "跳槽后确实成长很快，虽然前期有点累"
}
```

**响应：**
```json
{
  "preview": {
    "case_type": "career",
    "title": "三年产品的成长焦虑",
    "background": "某互联网公司工作三年，感觉重复劳动多...",
    "core_conflict": "成长空间 vs 稳定收入",
    "duration_days": 15,
    "final_choice": "接受了新 offer",
    "turning_point": "跟前辈聊天后意识到机会成本更高",
    "retrospect": "跳槽后确实成长很快...",
    "retrospect_score": 8,
    "retrospect_months": 3,
    "decision_style": "rational",
    "life_stage": "early_career",
    "tags": "职业发展,成长焦虑,跳槽"
  }
}
```

---

### POST `/api/cards/{card_id}/share/confirm`
确认发布案例到社区（写入数据库）

**请求体：**
```json
{
  "case_data": {
    "case_type": "career",
    "title": "三年产品的成长焦虑",
    "background": "某互联网公司工作三年...",
    "core_conflict": "成长空间 vs 稳定收入",
    "duration_days": 15,
    "final_choice": "接受了新 offer",
    "turning_point": "跟前辈聊天后意识到...",
    "retrospect": "跳槽后确实成长很快...",
    "retrospect_score": 8,
    "retrospect_months": 3,
    "decision_style": "rational",
    "life_stage": "early_career",
    "tags": "职业发展,成长焦虑,跳槽"
  }
}
```

**响应：**
```json
{
  "case_id": 42,
  "message": "已分享到社区"
}
```

---

## 记忆 API

### GET `/api/memories?uid={uid}&type={type}&limit={limit}`
查询用户记忆列表

**参数：**
- `uid`：用户 ID（必填）
- `type`：记忆类型，`episode`（情景记忆）或 `core`（核心档案）（必填）
- `limit`：返回数量，默认 20

**响应（type=episode）：**
```json
{
  "memories": [
    {
      "id": "mem_001",
      "content": "2024-06-16 用户提到对现在公司的成长空间不满，考虑跳槽",
      "tags": ["career", "growth"],
      "created_at": "2024-06-16T10:00:00"
    }
  ],
  "type": "episode"
}
```

**响应（type=core）：**
```json
{
  "memories": [
    {
      "content": "决策风格：理性分析型",
      "tags": ["profile", "decision_style"]
    },
    {
      "content": "核心价值观：成长、自由、稳定",
      "tags": ["profile", "values"]
    }
  ],
  "type": "core"
}
```

---

### PUT `/api/memories/core`
手动更新核心档案记忆

**请求体：**
```json
{
  "uid": "a1b2c3d4",
  "items": [
    {
      "content": "决策风格：直觉感知型",
      "tags": ["profile", "decision_style"]
    },
    {
      "content": "核心价值观：自由、成长、创新",
      "tags": ["profile", "values"]
    }
  ]
}
```

**响应：**
```json
{
  "ok": true
}
```

**说明：**
- 同时写入 Memosyne 远程 API 和本地数据库
- 本地数据库作为 fallback，保证 AI 对话能读到最新档案

---

### DELETE `/api/memories`
删除指定记忆

**请求体：**
```json
{
  "uid": "a1b2c3d4",
  "type": "episode",
  "memory_ids": ["mem_001", "mem_002"]
}
```

**响应：**
```json
{
  "ok": true
}
```

---

## 社区案例 API

### GET `/api/cases?type={type}&limit={limit}&offset={offset}`
获取社区案例列表（分页）

**参数：**
- `type`：筛选类型，`all` | `career` | `relationship` | `lifestyle` | `finance` | `education`
- `limit`：每页数量，默认 50，最大 100
- `offset`：分页偏移，默认 0

**响应：**
```json
{
  "cases": [
    {
      "id": 42,
      "case_type": "career",
      "title": "三年产品的成长焦虑",
      "background": "某互联网公司工作三年...",
      "core_conflict": "成长空间 vs 稳定收入",
      "duration_days": 15,
      "final_choice": "接受了新 offer",
      "turning_point": "跟前辈聊天后意识到机会成本更高",
      "retrospect": "跳槽后确实成长很快，虽然前期有点累",
      "retrospect_score": 8,
      "retrospect_months": 3,
      "decision_style": "rational",
      "life_stage": "early_career",
      "tags": "职业发展,成长焦虑,跳槽",
      "empathy_count": 12,
      "view_count": 156,
      "is_featured": 0,
      "is_user_contributed": 1,
      "created_at": "2024-06-16T20:00:00"
    }
  ],
  "total": 87,
  "has_more": true
}
```

---

### GET `/api/cases/recommendations?card_id={card_id}&limit={limit}`
为指定卡片推荐相似案例（纠结驱动）

**参数：**
- `card_id`：纠结卡片 ID（必填）
- `limit`：返回数量，默认 3，最大 10

**响应：**
```json
{
  "cases": [
    {
      "id": 12,
      "case_type": "career",
      "title": "三年产品经理的跳槽纠结",
      "core_conflict": "成长空间 vs 团队氛围",
      "final_choice": "最终选择了跳槽",
      "retrospect_score": 8,
      "_score": 5.5
    }
  ]
}
```

**说明：**
- 匹配逻辑：同 `dilemma_type` + 核心矛盾关键词重叠度 + 画像加权
- `_score` 为调试字段，显示匹配得分

---

### POST `/api/cases/{case_id}/empathy`
点击"我也是"，增加共鸣数

**响应：**
```json
{
  "empathy_count": 13
}
```

---

### POST `/api/cases/{case_id}/view`
增加案例浏览数（进入详情时调用）

**响应：**
```json
{
  "message": "ok"
}
```

---

## 错误响应格式

所有 API 错误统一返回格式：

```json
{
  "detail": "错误信息描述"
}
```

**常见错误码：**
- `400`：请求参数错误
- `401`：未授权（用户名或密码错误）
- `404`：资源不存在
- `500`：服务器内部错误
