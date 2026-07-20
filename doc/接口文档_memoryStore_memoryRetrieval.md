# 记忆存储与检索接口文档

## 1. memoryStore - 记忆存储接口

### 1.1 接口描述
将对话消息存储为不同类型的记忆（情景记忆、语义记忆、隐私记忆等）。系统会自动进行边界检测、记忆单元（MemCell）构建，并并发提取多种类型的记忆。

### 1.2 请求信息
- **接口路径**: `/v1/s/memosyne/memoryStore`
- **请求方法**: `POST`
- **Content-Type**: `application/json`

### 1.3 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| messages | Array<Message> | 是 | 对话消息列表 |
| memoryType | Array<String> | 是 | 记忆类型列表，支持：`core`（核心记忆）、`privacy`（隐私记忆）、`episode`（情景记忆）、`semantic`（语义记忆）、`procedural`（程序记忆） |
| appId | String | 是 | 应用ID |
| uid | String | 是 | 用户ID，长度不超过32字符 |
| agentId | String | 否 | 智能体ID |
| user | String | 否 | 用户名称，默认为"用户"（中文）或"user"（英文） |
| repoId | String | 是 | 仓库ID，用于定位存储集合 |
| language | String | 否 | 语言类型，支持 `ch`（中文）或 `en`（英文），默认为 `ch` |

#### Message 对象结构

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| role | String | 是 | 角色类型，`user`（用户）或 `assistant`（助手） |
| content | String | 是 | 消息内容 |
| timestamp | Int64 | 否 | 消息时间戳（毫秒），用于时间边界检测 |
| user | String | 否 | 说话人名称 |

### 1.4 请求示例

```json
{
  "messages": [
    {
      "role": "user",
      "content": "我最喜欢的颜色是蓝色",
      "timestamp": 1704067200000
    },
    {
      "role": "assistant",
      "content": "好的，我记住了您喜欢蓝色",
      "timestamp": 1704067201000
    }
  ],
  "memoryType": ["episode", "semantic", "privacy"],
  "appId": "app_001",
  "uid": "user_123",
  "agentId": "agent_001",
  "user": "张三",
  "repoId": "repo_001",
  "language": "ch"
}
```

### 1.5 响应参数

**成功响应**：HTTP 200
```json
null
```

**失败响应**：
```json
{
  "code": "错误码",
  "message": "错误描述信息"
}
```

### 1.6 处理流程

1. **消息分批**：按时间跨度（3天）和长度限制自动分批处理
2. **边界检测**：识别对话中的记忆边界，构建记忆单元（MemCell）
3. **并发提取**：
   - **情景记忆（episode）**：提取对话场景和事件
   - **语义记忆（semantic）**：提取实体和关系
   - **隐私记忆（privacy）**：提取用户隐私信息
4. **持久化存储**：将提取的记忆存储到对应的数据库集合

### 1.7 注意事项

- uid 长度必须 ≤ 32 字符
- 消息列表会按时间跨度（超过3天）或长度限制自动分批
- 支持并发提取多种记忆类型，提高处理效率
- 如果某个记忆类型提取失败，不影响其他类型的提取

---

## 2. memoryRetrieval - 记忆检索接口

### 2.1 接口描述
根据对话上下文检索相关记忆。支持两种检索模式：快速检索（quickRetrieval）和慢思考检索（slowThinking）。

### 2.2 请求信息
- **接口路径**: `/v1/s/memosyne/memoryRetrieval`
- **请求方法**: `POST`
- **Content-Type**: `application/json`

### 2.3 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| messages | Array<Message> | 是 | 对话消息列表，用于检索上下文 |
| retrievalMode | String | 是 | 检索模式：`quickRetrieval`（快速检索）或 `slowThinking`（慢思考检索） |
| appId | String | 是 | 应用ID |
| uid | String | 是 | 用户ID，长度不超过32字符 |
| agentId | String | 否 | 智能体ID |
| repoId | String | 是 | 仓库ID |
| memoryType | Array<String> | 否 | 要检索的记忆类型列表，默认为所有类型 |
| topN | Int | 否 | 返回的记忆条数，默认值根据配置 |
| threshold | Float | 否 | 相似度阈值（0-1），低于此值的记忆不返回 |
| depth | Int | 否 | 慢思考模式下的检索深度（迭代轮数），默认为1 |
| stream | Boolean | 否 | 是否使用流式返回（仅慢思考模式），默认 false |
| returnIntermediateSteps | Boolean | 否 | 是否返回中间步骤（仅慢思考模式），默认 false |
| conflictDetection | Boolean | 否 | 是否进行冲突检测，默认 false |
| planPrompt | String | 否 | 自定义规划提示词（仅慢思考模式） |
| language | String | 否 | 语言类型，支持 `ch` 或 `en`，默认为 `ch` |
| match | Match | 否 | 各记忆类型的过滤条件，**当前仅 quickRetrieval 模式生效** |

#### Match 对象结构

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| episode | EpisodeMatch | 否 | 情景记忆的过滤条件 |

#### EpisodeMatch 对象结构

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| startTime | String | 否 | 对话时间范围起点，格式 `YYYY-MM-DD`，按 `dialogTime >= startTime` 过滤 |
| endTime | String | 否 | 对话时间范围终点，格式 `YYYY-MM-DD`，按 `dialogTime <= endTime` 过滤（含当天） |
| subType | String | 否 | 情景记忆子类型限制；不传则返回 episode 与 cluster 两类 |

**subType 取值说明**

| 取值 | 说明 |
|------|------|
| `episode` | 只返回原始情景记忆，不展开也不返回关联的 cluster |
| `cluster` | 只返回事件链，不展开也不返回关联的 episode |
| 不传 | 默认行为：episode 命中时附带其所属 cluster；cluster 命中时展开最近 3 条 episode |

### 2.4 请求示例

#### 快速检索模式
```json
{
  "messages": [
    {
      "role": "user",
      "content": "我喜欢什么颜色？"
    }
  ],
  "retrievalMode": "quickRetrieval",
  "appId": "app_001",
  "uid": "user_123",
  "agentId": "agent_001",
  "repoId": "repo_001",
  "memoryType": ["privacy", "semantic"],
  "topN": 5,
  "language": "ch"
}
```

#### 快速检索模式（携带 match 过滤条件）
```json
{
  "messages": [
    {
      "role": "user",
      "content": "今年3月我做了什么？"
    }
  ],
  "retrievalMode": "quickRetrieval",
  "appId": "app_001",
  "uid": "user_123",
  "repoId": "repo_001",
  "memoryType": ["episode"],
  "topN": 5,
  "language": "ch",
  "match": {
    "episode": {
      "startTime": "2025-03-01",
      "endTime": "2025-03-31",
      "subType": "episode"
    }
  }
}
```

#### 慢思考检索模式（非流式）
```json
{
  "messages": [
    {
      "role": "user",
      "content": "我上次和你聊了什么？"
    }
  ],
  "retrievalMode": "slowThinking",
  "appId": "app_001",
  "uid": "user_123",
  "repoId": "repo_001",
  "memoryType": ["episode", "semantic"],
  "depth": 3,
  "stream": false,
  "language": "ch"
}
```

#### 慢思考检索模式（流式）
```json
{
  "messages": [
    {
      "role": "user",
      "content": "帮我回忆一下我们之前讨论的项目"
    }
  ],
  "retrievalMode": "slowThinking",
  "appId": "app_001",
  "uid": "user_123",
  "repoId": "repo_001",
  "depth": 2,
  "stream": true,
  "language": "ch"
}
```

### 2.5 响应参数

#### 快速检索模式响应
```json
{
  "memories": [
    {
      "type": "privacy",
      "content": "用户喜欢的颜色是蓝色",
      "score": 0.95
    },
    {
      "type": "semantic",
      "content": "实体：蓝色，关系：喜欢",
      "score": 0.88
    }
  ]
}
```

#### 慢思考模式响应（非流式）
```json
{
  "steps": [
    "分析用户问题：需要检索历史对话记忆",
    "调用工具：retrieval_episode_memory",
    "找到3条相关情景记忆"
  ],
  "result": [
    "2024-01-01：讨论了项目A的技术方案",
    "2024-01-05：确定了项目时间表",
    "2024-01-10：分配了团队成员任务"
  ]
}
```

#### 慢思考模式响应（流式）
流式返回，每个数据块格式：
```json
{
  "message": "thinking",
  "data": {
    "thinking": "正在分析用户问题..."
  }
}
```
或
```json
{
  "message": "result",
  "data": {
    "result": ["检索到的记忆内容"]
  }
}
```

### 2.6 检索模式说明

#### quickRetrieval（快速检索）
- 直接基于向量相似度检索
- 速度快，适合实时对话场景
- 返回 topN 条最相关的记忆

#### slowThinking（慢思考检索）
- 使用大模型进行多轮推理和工具调用
- 可以进行复杂的记忆组合和推理
- 支持流式返回中间思考过程
- 适合需要深度理解和复杂查询的场景
- 通过 depth 参数控制推理深度（迭代轮数）

### 2.7 注意事项

- uid 长度必须 ≤ 32 字符
- messages 不能为空
- retrievalMode 必须是 `quickRetrieval` 或 `slowThinking`
- 慢思考模式会自动获取用户基础画像信息
- 流式模式仅在慢思考模式下有效
- 检索结果会根据相似度排序
- `match` 参数当前仅在 `quickRetrieval` 模式下生效
- `match.episode.startTime` / `endTime` 按情景记忆的**对话时间**（dialogTime）过滤，与记忆入库时间无关
- `match.episode.subType` 为 `episode` 时不展开 cluster；为 `cluster` 时不展开 episode；两个方向完全隔离

---

## 3. 记忆类型说明

| 记忆类型 | 英文标识 | 说明 |
|---------|---------|------|
| 核心记忆 | core | 用户的基础画像、兴趣偏好、人格特征等长期稳定的信息 |
| 隐私记忆 | privacy | 用户的个人隐私信息，如姓名、联系方式等 |
| 情景记忆 | episode | 具体的对话场景和事件记录 |
| 语义记忆 | semantic | 从对话中提取的实体和实体间的关系 |
| 程序记忆 | procedural | 用户的操作习惯和流程性知识 |

## 4. 错误码说明

| 错误码 | 说明 |
|--------|------|
| RequestBodyError | 请求参数错误 |
| StoreOfflineResultError | 记忆存储失败 |
| DatabaseExecError | 数据库操作失败 |
| CallLLMError | 大模型调用失败 |

---

## 5. memoryStoreOffline - 离线记忆构建接口

### 5.1 接口描述

异步版本的记忆存储接口。请求会被立即入队并返回任务 ID，实际的记忆提取与存储由后台 Worker 异步执行，不阻塞调用方。

与 `memoryStore` 的主要区别：

| 对比项 | memoryStore | memoryStoreOffline |
|--------|-------------|-------------------|
| 执行方式 | 同步，等待完成后返回 | 异步，立即返回任务 ID |
| 幂等性 | 无 | 有，1 小时内相同请求只处理一次 |
| 适用场景 | 对话结束后实时写入 | 批量导入、低优先级补录 |

### 5.2 请求信息

- **接口路径**: `/v1/s/memosyne/memoryStoreOffline`
- **请求方法**: `POST`
- **Content-Type**: `application/json`

### 5.3 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| messages | Array<Message> | 是 | 对话消息列表 |
| memoryType | Array<String> | 否 | 记忆类型列表，支持：`core`、`privacy`、`episode`、`semantic`、`procedural`；不传则提取全部类型 |
| appId | String | 是 | 应用ID |
| uid | String | 是 | 用户ID，长度不超过32字符 |
| agentId | String | 否 | 智能体ID |
| user | String | 否 | 用户名称，默认"用户"（中文）或"user"（英文） |
| repoId | String | 是 | 仓库ID，用于定位存储集合 |
| language | String | 否 | 语言类型，`ch`（中文）或 `en`（英文），默认 `ch` |

Message 对象结构同 [memoryStore](#14-请求示例)。

### 5.4 幂等性说明

系统会对请求计算唯一指纹（基于 `appId + uid + agentId + repoId + memoryType + messages 内容` 的 SHA-256），并在 Redis 中以 **1 小时 TTL** 缓存。

- **首次提交**：正常入队，返回 `taskId`
- **1 小时内重复提交相同请求**：刷新 TTL、丢弃任务、返回 `taskId: "duplicate"`（HTTP 状态码仍为 200）
- **幂等性功能通过配置开关控制**，关闭时不做去重直接入队

### 5.5 请求示例

```json
{
  "messages": [
    {
      "role": "user",
      "content": "我今天去了故宫，非常震撼",
      "timestamp": 1714060800000
    },
    {
      "role": "assistant",
      "content": "故宫是很有历史价值的地方，您有什么特别的感受吗？",
      "timestamp": 1714060810000
    }
  ],
  "memoryType": ["episode", "semantic"],
  "appId": "app_001",
  "uid": "user_123",
  "agentId": "agent_001",
  "user": "张三",
  "repoId": "repo_001",
  "language": "ch"
}
```

### 5.6 响应参数

**成功响应**（HTTP 200）：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| taskId | String | 任务 ID，可用于日志追踪；值为 `"duplicate"` 时表示本次为重复请求已被丢弃 |

```json
{
  "code": 0,
  "data": {
    "taskId": "app_001_user_123_1714060800000000000"
  }
}
```

**重复请求响应**（HTTP 200）：

```json
{
  "code": 0,
  "data": {
    "taskId": "duplicate"
  }
}
```

**失败响应**：

```json
{
  "code": 错误码,
  "message": "错误描述信息"
}
```

### 5.7 注意事项

- uid 长度必须 ≤ 32 字符
- messages 不能为空
- 任务入队后由后台 Worker 异步处理，**接口返回成功不代表记忆已写入**，实际写入有一定延迟
- 幂等判断基于请求内容的 SHA-256 指纹，**任何字段变化（含消息顺序）都视为不同请求**
- 重复请求返回 HTTP 200 而非错误码，调用方无需特殊处理
