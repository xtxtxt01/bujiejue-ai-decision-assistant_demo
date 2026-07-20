# Memosyne 记忆系统 API 接口手册（App 开发用）

## 快速概览

| 记忆类型 | 服务地址 | 核心能力 | 典型场景 |
|----------|---------|---------|---------|
| 情景记忆 (Episode) | `http://172.16.154.251:21004` | 对话事件存储与语义检索 | "我之前说过什么" |
| 语义记忆 (Semantic) | `http://172.16.154.251:21004` | 知识图谱、实体关系 | "用户喜欢什么" |
| 程序记忆 (Procedural) | `http://10.6.41.6:16666` | 行为模式学习与推荐 | "现在该推荐什么操作" |

---

## 一、情景记忆 + 语义记忆（共用接口）

情景记忆和语义记忆共用同一套 HTTP 接口，通过 `memoryType` 字段区分。

### 基础地址

```
BASE_URL = "http://172.16.154.251:21004"
```

### 公共参数

每个请求都需要以下字段：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| appId | string | 是 | 应用 ID（纯字母数字，不含下划线） |
| uid | string | 是 | 用户 ID（最大 32 字符） |
| agentId | string | 是 | 智能体 ID |
| repoId | string | 是 | 知识库 ID |

---

### 1.1 存储记忆（自动提取）

系统从对话消息中 **自动** 提取情景记忆和语义记忆。

```
POST /v1/s/memosyne/memoryStore
```

**请求示例：**

```python
import requests

url = "http://172.16.154.251:21004/v1/s/memosyne/memoryStore"

payload = {
    "appId": "myapp001",
    "uid": "user001",
    "agentId": "agent001",
    "repoId": "repo001",
    "memoryType": ["episode", "semantic"],  # 同时提取两种记忆
    "messages": [
        {"role": "user", "content": "我最近在学吉他，已经学了三个月了"},
        {"role": "assistant", "content": "学吉他很有意思，你学的是民谣还是电吉他？"},
        {"role": "user", "content": "民谣吉他，主要弹唱。我特别喜欢周杰伦的歌"}
    ]
}

resp = requests.post(url, json=payload)
print(resp.json())
# {"code": 0, "message": "success", "data": {...}}
```

**memoryType 选项：**
- `["episode"]` — 只提取事件（"用户在学吉他"）
- `["semantic"]` — 只提取实体关系（"用户 → 喜欢 → 周杰伦"）
- `["episode", "semantic"]` — 两种都提取（推荐）

**注意：** 存储是异步的，写入后需等待 ~5 秒才能检索到。

---

### 1.2 手动写入记忆（结构化写入）

直接写入结构化的记忆，无需系统提取。适合导入已有数据。

```
POST /v1/s/memosyne/memoryUpsert
```

**请求示例：**

```python
payload = {
    "appId": "myapp001",
    "uid": "user001",
    "agentId": "agent001",
    "repoId": "repo001",
    "episode": [
        {
            "id": "ep_001",
            "title": "学习吉他",
            "content": "用户在学民谣吉他弹唱，已经学了三个月",
            "tags": ["音乐", "学习"],
            "timestamp": 1718380800000,  # 毫秒时间戳
            "atomicFact": ["用户在学吉他", "学了三个月", "民谣吉他弹唱"]
        }
    ],
    "core": {
        "兴趣偏好": {
            "category": "音乐爱好",
            "items": [
                {"content": "喜欢周杰伦的歌", "tags": ["音乐"]},
                {"content": "在学民谣吉他", "tags": ["音乐"]}
            ]
        }
    }
}

resp = requests.post(f"{BASE_URL}/v1/s/memosyne/memoryUpsert", json=payload)
```

---

### 1.3 检索记忆（核心接口）

根据当前对话语义，检索相关的历史记忆。**这是 App 最常用的接口。**

```
POST /v1/s/memosyne/memoryRetrieval
```

**请求示例（检索所有类型）：**

```python
payload = {
    "appId": "myapp001",
    "uid": "user001",
    "agentId": "agent001",
    "repoId": "repo001",
    "retrievalMode": "quickRetrieval",
    "messages": [
        {"role": "user", "content": "给我推荐一首歌吧"}
    ],
    "memoryType": ["episode", "semantic", "core"],  # 检索所有类型
    "topN": 5,          # 返回 5 条最相关的记忆
    "threshold": 0.3,   # 相似度阈值（越低召回越多）
    "getBasicInfo": True # 同时返回用户基础信息
}

resp = requests.post(f"{BASE_URL}/v1/s/memosyne/memoryRetrieval", json=payload)
data = resp.json()["data"]

# 格式化的记忆文本（可直接拼入 prompt）
memory_text = "\n".join(data["result"])

# 结构化记忆条目（可自定义处理）
for item in data["items"]:
    print(f"[{item['type']}] score={item['score']:.2f}: {item.get('content', '')}")

# 用户基础信息
basic_info = data.get("basicInfo", "")
```

**响应示例：**

```json
{
  "code": 0,
  "data": {
    "result": [
      "【事件】\n学习吉他:用户在学民谣吉他弹唱，已经学了三个月",
      "用户喜欢周杰伦的歌"
    ],
    "items": [
      {
        "score": 0.91,
        "type": "episode",
        "episode": {
          "id": "ep_001",
          "title": "学习吉他",
          "content": "用户在学民谣吉他弹唱，已经学了三个月",
          "tags": ["音乐"]
        }
      },
      {
        "score": 0.87,
        "type": "semantic",
        "content": "用户喜欢周杰伦的歌"
      }
    ],
    "basicInfo": "姓名：张三\n年龄：28岁"
  }
}
```

---

### 1.4 检索记忆（条件查询）

不走语义检索，直接按条件过滤。适合"查看某时间段的记忆"等场景。

```
POST /v1/s/memosyne/memoryRetrieval
```

**请求示例（条件检索 — messages 为空）：**

```python
payload = {
    "appId": "myapp001",
    "uid": "user001",
    "agentId": "agent001",
    "repoId": "repo001",
    "retrievalMode": "quickRetrieval",
    "messages": [],  # 空 = 条件检索模式
    "memoryType": ["episode"],
    "topN": 10,
    "match": {
        "episode": {
            "tags": {"must": ["音乐"]},       # 标签必须含"音乐"
            "startTime": "2024-06-01",         # 时间范围
            "endTime": "2024-12-31",
            "subType": "episode"               # 只要原始片段，不要 cluster
        }
    }
}
```

---

### 1.5 查询记忆（MongoDB 直接查询）

```
POST /v1/s/memosyne/memoryQuery
```

```python
payload = {
    "appId": "myapp001",
    "uid": "user001",
    "agentId": "agent001",
    "repoId": "repo001",
    "memoryType": "episode",  # 或 "core"
    "limit": 20,
    "match": {
        "episode": {
            "tags": {"must": ["工作"], "should": ["项目", "会议"]}
        }
    }
}

resp = requests.post(f"{BASE_URL}/v1/s/memosyne/memoryQuery", json=payload)
episodes = resp.json()["data"]["episodes"]
```

---

### 1.6 删除记忆

```
DELETE /v1/s/memosyne/memoryDelete
```

```python
payload = {
    "appId": "myapp001",
    "uid": "user001",
    "agentId": "agent001",
    "repoId": "repo001",
    "memoryType": "episode",
    "memoryIds": ["ep_001", "ep_002"]  # 要删除的 ID
}

resp = requests.delete(f"{BASE_URL}/v1/s/memosyne/memoryDelete", json=payload)
```

---

### 1.7 典型 App 集成模式

```python
class MemoryClient:
    """记忆系统客户端封装"""
    
    def __init__(self, app_id, uid, agent_id="default", repo_id="default"):
        self.base_url = "http://172.16.154.251:21004"
        self.common = {
            "appId": app_id,
            "uid": uid,
            "agentId": agent_id,
            "repoId": repo_id
        }
    
    def store(self, messages, memory_types=None):
        """对话后存储记忆"""
        payload = {
            **self.common,
            "memoryType": memory_types or ["episode", "semantic"],
            "messages": messages
        }
        return requests.post(
            f"{self.base_url}/v1/s/memosyne/memoryStore", json=payload
        ).json()
    
    def retrieve(self, user_message, top_n=5, threshold=0.3):
        """对话前检索相关记忆"""
        payload = {
            **self.common,
            "retrievalMode": "quickRetrieval",
            "messages": [{"role": "user", "content": user_message}],
            "memoryType": ["episode", "semantic", "core"],
            "topN": top_n,
            "threshold": threshold,
            "getBasicInfo": True
        }
        resp = requests.post(
            f"{self.base_url}/v1/s/memosyne/memoryRetrieval", json=payload
        ).json()
        return resp.get("data", {})
    
    def build_prompt_with_memory(self, user_message, system_prompt=""):
        """带记忆的 prompt 构建"""
        memory_data = self.retrieve(user_message)
        
        memory_text = ""
        if memory_data.get("result"):
            memory_text = "\n".join(memory_data["result"])
        if memory_data.get("basicInfo"):
            memory_text = f"用户信息：{memory_data['basicInfo']}\n\n记忆：\n{memory_text}"
        
        full_prompt = f"""{system_prompt}

## 用户记忆（以下是你对该用户的了解）
{memory_text}

## 当前对话
用户：{user_message}
"""
        return full_prompt


# 使用示例
client = MemoryClient(app_id="myapp001", uid="user001")

# 1. 用户发消息 → 检索记忆 → 增强 prompt
prompt = client.build_prompt_with_memory("给我推荐一首歌")
# 把 prompt 发给 LLM 生成回复...

# 2. 对话结束 → 存储本轮对话
client.store([
    {"role": "user", "content": "给我推荐一首歌"},
    {"role": "assistant", "content": "根据你喜欢周杰伦，推荐《晴天》"}
])
```

---

## 二、程序记忆（独立接口）

程序记忆用于学习用户的 **行为模式**，在相似场景下推荐操作。典型应用：智能座舱、智能家居、个性化工作流。

### 基础地址

```
BASE_URL = "http://10.6.41.6:16666"
```

---

### 2.1 构建记忆（记录用户行为）

每次用户执行操作时调用，系统积累后学习行为模式。

```
POST /memory/build
```

**请求示例：**

```python
import requests
from datetime import datetime

url = "http://10.6.41.6:16666/memory/build"

payload = {
    # 用户标识
    "user_id": "myapp001_user001_randomstr",  # 格式: appid_userid_随机串
    
    # 会话 ID（每次交互是一个 session）
    "session_id": "session_20260615_0830",
    
    # 当前状态（描述当前环境/上下文）
    "state": [
        "car:start",               # 车辆状态
        "weather:sunny",           # 天气
        "inside_temp:comfortable", # 车内温度
        "outdoor_temp:comfortable" # 车外温度
        # 系统自动推导: day_type, weekday, daypart, time_bucket
    ],
    
    # 用户执行的操作
    "tools": [
        {
            "name": "navigate_to({\"destination\":\"公司\"})",
            "timestamp": "2026-06-15T08:30:00+08:00"
        }
    ],
    
    # 时间戳（毫秒）
    "time": int(datetime(2026, 6, 15, 8, 30).timestamp() * 1000),
    
    # 作用域
    "scope": "family"  # family=家庭共享, exact=仅自己
}

resp = requests.post(url, json=payload)
print(resp.json())
```

**state 维度说明：**

| 维度 | 可选值 | 说明 |
|------|--------|------|
| car | start / run / stop | 车辆状态（必传） |
| weather | sunny / cloudy / rainy / snowy | 天气 |
| inside_temp | cold / cool / comfortable / hot / very_hot | 车内温度 |
| outdoor_temp | cold / cool / comfortable / hot / very_hot | 车外温度 |
| passenger | 乘客名字 | 可以有多个 passenger:xxx |

**不需要手动传的维度**（系统从 time 自动推导）：
- `day_type`：workday / weekend / holiday
- `weekday`：mon / tue / wed / thu / fri / sat / sun
- `daypart`：morning / afternoon / evening / night
- `time_bucket`：morning_commute / afternoon / evening_commute / night

---

### 2.2 检索推荐（获取推荐操作）

根据当前状态，推荐用户可能想做的操作。

```
POST /memory/retrieve
```

**请求示例：**

```python
payload = {
    "user_id": "myapp001_user001_randomstr",
    
    # 当前状态
    "state": [
        "car:start",
        "weather:sunny",
        "inside_temp:comfortable",
        "outdoor_temp:comfortable"
    ],
    
    # 强匹配状态（这些必须完全匹配）
    "strong_match_state": [
        "car:start"  # 只推荐"启动"状态下的操作
    ],
    
    # 已执行的操作（用于去重和工具链推荐）
    "tool_history": [],  # 空=还没做任何操作
    
    # 时间
    "time": int(datetime(2026, 6, 15, 8, 30).timestamp() * 1000),
    
    # 返回数量
    "top_k": 5,
    
    # 是否返回调试信息
    "include_debug": True
}

resp = requests.post(f"{BASE_URL}/memory/retrieve", json=payload)
data = resp.json()

# 解析推荐结果
for rec in data["recommendations"]:
    print(f"推荐: {rec['tool_name']}")
    print(f"  得分: {rec['score']:.4f}")
    print(f"  理由: {rec.get('reason', '')}")
    if rec.get("debug"):
        print(f"  匹配类型: {rec['debug']['match_type']}")
        print(f"  置信度: {rec['debug']['confidence_level']}")
```

**响应示例：**

```json
{
  "recommendations": [
    {
      "tool_name": "navigate_to({\"destination\":\"公司\"})",
      "score": 0.8234,
      "reason": "工作日早上启动车时，你通常会导航去公司",
      "debug": {
        "match_type": "time_pattern_match",
        "confidence_level": "high",
        "evidence": {
          "history_count": 8,
          "state_match": {"coverage": 0.85}
        },
        "score": {
          "factors": {
            "source_weight": 0.4,
            "state_match_weight": 0.85,
            "support_weight": 1.0,
            "count_weight": 2.197,
            "recency_weight": 0.91
          }
        }
      }
    }
  ]
}
```

**匹配类型说明：**

| 类型 | 说明 | 触发条件 |
|------|------|---------|
| exact_match | 状态完全一致 | 精确匹配所有维度 |
| strong_state_match | 核心状态匹配 | strong_match_state 全部命中 |
| weak_state_match | 部分状态匹配 | 部分维度匹配 |
| time_pattern_match | 时间模式匹配 | 同一时段有重复行为 |
| tool_sequence_match | 工具链匹配 | tool_history 命中序列 |

---

### 2.3 查看已有记忆

```
GET /memory/show?user_id=myapp001_user001_randomstr
```

```python
resp = requests.get(f"{BASE_URL}/memory/show", params={"user_id": "myapp001_user001_randomstr"})
memories = resp.json()
```

---

### 2.4 清除记忆

```
DELETE /memory/clean
```

```python
payload = {"user_id": "myapp001_user001_randomstr"}
resp = requests.delete(f"{BASE_URL}/memory/clean", json=payload)
```

---

### 2.5 典型 App 集成模式

```python
class ProceduralMemoryClient:
    """程序记忆客户端"""
    
    def __init__(self, app_id, user_id):
        self.base_url = "http://10.6.41.6:16666"
        self.user_id = f"{app_id}_{user_id}_demo"
    
    def record_action(self, state, tool_name, tool_params=None):
        """记录一次用户操作"""
        from datetime import datetime
        now = datetime.now()
        
        tool_str = tool_name
        if tool_params:
            import json
            tool_str = f"{tool_name}({json.dumps(tool_params, ensure_ascii=False)})"
        
        payload = {
            "user_id": self.user_id,
            "session_id": f"session_{now.strftime('%Y%m%d_%H%M%S')}",
            "state": state,
            "tools": [{"name": tool_str, "timestamp": now.isoformat()}],
            "time": int(now.timestamp() * 1000),
            "scope": "exact"
        }
        return requests.post(f"{self.base_url}/memory/build", json=payload).json()
    
    def get_recommendations(self, state, strong_match=None, tool_history=None, top_k=3):
        """获取推荐操作"""
        from datetime import datetime
        
        payload = {
            "user_id": self.user_id,
            "state": state,
            "strong_match_state": strong_match or [state[0]],
            "tool_history": tool_history or [],
            "time": int(datetime.now().timestamp() * 1000),
            "top_k": top_k,
            "include_debug": False
        }
        resp = requests.post(f"{self.base_url}/memory/retrieve", json=payload).json()
        return resp.get("recommendations", [])


# 使用示例
client = ProceduralMemoryClient("myapp", "user001")

# 1. 记录用户行为（每次用户操作时调用）
client.record_action(
    state=["car:start", "weather:sunny", "inside_temp:comfortable"],
    tool_name="navigate_to",
    tool_params={"destination": "公司"}
)

# 2. 获取推荐（在相似场景下）
recs = client.get_recommendations(
    state=["car:start", "weather:sunny", "inside_temp:comfortable"],
    strong_match=["car:start"]
)
for r in recs:
    print(f"推荐：{r['tool_name']}（得分 {r['score']:.2f}）")
```

---

## 三、三种记忆的协同使用

### 3.1 完整个性化 App 架构

```
┌─────────────────────────────────────────────────┐
│                  用户交互层                        │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌─────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ 对话前  │  │   对话中     │  │  对话后     │  │
│  │         │  │             │  │             │  │
│  │ 检索记忆│  │ LLM 生成    │  │ 存储记忆    │  │
│  │ ↓       │  │ (带记忆     │  │ ↓           │  │
│  │ 增强    │  │  context)   │  │ episode +   │  │
│  │ prompt  │  │             │  │ semantic    │  │
│  └────┬────┘  └─────────────┘  └──────┬──────┘  │
│       │                                │         │
├───────┼────────────────────────────────┼─────────┤
│       ▼                                ▼         │
│  ┌─────────────────────────────────────────────┐ │
│  │           Memosyne 记忆平台                  │ │
│  ├─────────┬───────────────┬───────────────────┤ │
│  │Episode  │   Semantic    │   Procedural      │ │
│  │事件记忆  │  知识图谱      │   行为推荐         │ │
│  │"发生了   │ "用户是谁，    │  "该推荐什么       │ │
│  │ 什么"   │  喜欢什么"    │   操作"            │ │
│  └─────────┴───────────────┴───────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 3.2 完整集成示例

```python
import requests
from datetime import datetime


class PersonalizedApp:
    """个性化 App Demo — 三种记忆协同"""
    
    def __init__(self, app_id, user_id):
        self.app_id = app_id
        self.user_id = user_id
        self.memory_url = "http://172.16.154.251:21004"
        self.procedural_url = "http://10.6.41.6:16666"
        self.common = {
            "appId": app_id,
            "uid": user_id,
            "agentId": "app_agent",
            "repoId": "app_repo"
        }
    
    # ========== 对话前：检索记忆 ==========
    
    def recall(self, user_message):
        """检索与当前对话相关的所有记忆"""
        payload = {
            **self.common,
            "retrievalMode": "quickRetrieval",
            "messages": [{"role": "user", "content": user_message}],
            "memoryType": ["episode", "semantic", "core"],
            "topN": 5,
            "threshold": 0.3,
            "getBasicInfo": True
        }
        resp = requests.post(
            f"{self.memory_url}/v1/s/memosyne/memoryRetrieval", json=payload
        )
        return resp.json().get("data", {})
    
    # ========== 对话后：存储记忆 ==========
    
    def remember(self, messages):
        """将本轮对话存入情景记忆和语义记忆"""
        payload = {
            **self.common,
            "memoryType": ["episode", "semantic"],
            "messages": messages
        }
        return requests.post(
            f"{self.memory_url}/v1/s/memosyne/memoryStore", json=payload
        ).json()
    
    # ========== 行为推荐：程序记忆 ==========
    
    def record_behavior(self, context_state, action_name, action_params=None):
        """记录用户行为（程序记忆学习）"""
        import json
        now = datetime.now()
        tool_str = action_name
        if action_params:
            tool_str = f"{action_name}({json.dumps(action_params, ensure_ascii=False)})"
        
        payload = {
            "user_id": f"{self.app_id}_{self.user_id}_app",
            "session_id": f"s_{now.strftime('%Y%m%d_%H%M%S')}",
            "state": context_state,
            "tools": [{"name": tool_str, "timestamp": now.isoformat()}],
            "time": int(now.timestamp() * 1000),
            "scope": "exact"
        }
        return requests.post(f"{self.procedural_url}/memory/build", json=payload).json()
    
    def suggest_actions(self, context_state, top_k=3):
        """基于当前上下文推荐操作（程序记忆推荐）"""
        payload = {
            "user_id": f"{self.app_id}_{self.user_id}_app",
            "state": context_state,
            "strong_match_state": [context_state[0]] if context_state else [],
            "tool_history": [],
            "time": int(datetime.now().timestamp() * 1000),
            "top_k": top_k
        }
        resp = requests.post(f"{self.procedural_url}/memory/retrieve", json=payload)
        return resp.json().get("recommendations", [])
    
    # ========== 组合使用 ==========
    
    def chat_with_memory(self, user_message, llm_call_fn):
        """
        带记忆的完整对话流程
        
        Args:
            user_message: 用户消息
            llm_call_fn: LLM 调用函数 fn(prompt) -> str
        """
        # 1. 检索相关记忆
        memory = self.recall(user_message)
        
        # 2. 构建增强 prompt
        memory_text = "\n".join(memory.get("result", []))
        basic_info = memory.get("basicInfo", "")
        
        prompt = f"""你是一个个性化助手。以下是你对用户的了解：

用户信息：{basic_info}

相关记忆：
{memory_text}

请基于以上记忆，个性化地回答用户的问题。

用户：{user_message}
助手："""
        
        # 3. 调用 LLM
        response = llm_call_fn(prompt)
        
        # 4. 存储本轮对话
        self.remember([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response}
        ])
        
        return response


# ========== 使用示例 ==========

app = PersonalizedApp("myapp001", "zhangsan")

# 场景 1：带记忆的对话
def my_llm(prompt):
    # 替换为你的 LLM 调用
    return "根据你之前说喜欢周杰伦，推荐《晴天》"

reply = app.chat_with_memory("给我推荐一首歌", my_llm)

# 场景 2：记录用户行为 + 获取推荐
app.record_behavior(
    context_state=["app:open", "time:morning"],
    action_name="open_playlist",
    action_params={"playlist": "工作专注"}
)

suggestions = app.suggest_actions(["app:open", "time:morning"])
# → 推荐: open_playlist({"playlist": "工作专注"})
```

---

## 四、注意事项

### 4.1 接口约束

| 约束 | 说明 |
|------|------|
| appId | **纯字母数字**，不能含下划线/连字符 |
| uid | 最长 32 字符 |
| 存储延迟 | 写入后 ~5 秒才能检索到 |
| topN | 建议 ≤ 15，过大影响性能 |
| threshold | 0.2~0.7，越低召回越多但噪声也多 |
| shareUids | 群组检索最多 5 个用户 |

### 4.2 推荐配置

**情景+语义记忆（对话场景）：**
```python
{
    "memoryType": ["episode", "semantic", "core"],
    "topN": 5,
    "threshold": 0.3,
    "getBasicInfo": True
}
```

**程序记忆（行为推荐）：**
- 每种场景至少记录 3 次以上才会生效（min_support=3）
- `strong_match_state` 只放不需要转换的字段（如 `car:start`、`app:open`）
- 避免放数值类字段（如 `temperature:15`，会被系统转枚举导致匹配失败）

### 4.3 典型调用时序

```
用户打开 App
    │
    ├─ 程序记忆: suggest_actions() → 推荐快捷操作
    │
用户发消息
    │
    ├─ 情景+语义: recall() → 检索相关记忆
    ├─ 构建 prompt（记忆 + 用户消息）
    ├─ 调用 LLM → 生成回复
    │
对话结束
    │
    ├─ 情景+语义: remember() → 存储本轮对话
    ├─ 程序记忆: record_behavior() → 记录用户操作
```
