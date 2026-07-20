# 不纠结 - AI 个性化决策助手

> **帮用户「看清自己是怎么做决定的」的 AI 工具**  
> 通过长期追踪纠结过程，发现你自己都没意识到的决策模式

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [目录结构](#目录结构)
- [核心模块详解](#核心模块详解)
- [配置说明](#配置说明)
- [开发指南](#开发指南)

---

## 🎯 项目简介

**不纠结**是一个基于 AI 的个性化决策辅助系统，核心差异不在于"有没有记忆"，而在于**记忆的用途和深度**：

- ✅ **不是**：通用 AI 助手（豆包/Kimi）的记忆只服务于"让回答更贴合你"
- ✅ **而是**：追踪你的完整决策历史，发现反复出现的模式，在下次犹豫时提供基于你自身历史的洞察

### 🎨 产品定位

| 维度 | 定位 |
|------|------|
| **目标用户** | 22-35 岁城市知识工作者（职业决策、关系选择、成长方向） |
| **核心场景** | 人生方向类、工作决策类、关系处理类纠结（非日常消费） |
| **价值主张** | 从表层痛点获客（纠结时没人商量）→ 中层留存（决定后不确定对不对）→ 深层壁垒（发现决策模式） |

---

## ✨ 核心特性

### 1. 🧠 **深度个性化对话系统**

- **GDMS 决策风格适配**：理性分析型、直觉感知型、参考借鉴型、审慎观望型、果断行动型，支持组合型风格
- **Maximizer 倾向识别**：追求最优型 vs 务实满意型 vs 灵活权衡型
- **价值观冲突检测**：实时对比用户声称的价值观排序与实际关注点，发现深层冲突
- **MBTI 适配策略**：针对 16 种人格类型定制对话策略

### 2. 🔄 **智能阶段驱动**

系统根据对话进度自动切换 4 个阶段：

| 阶段 | 触发条件 | 核心任务 |
|------|---------|---------|
| **Clarifying（追问）** | 前 3 轮且卡片无结构化信息 | 提取核心矛盾、触发事件、主要担忧 |
| **Exploring（探索）** | 信息不足以给建议 | 多维度探索用户真实需求、价值观权衡 |
| **Advising（建议）** | LLM 判断信息充足 / 用户主动询问 | 基于用户画像和历史决策给出个性化建议 |
| **Closing（收尾）** | 用户做出决定 / 手动关闭 | 生成 Insight 洞察、引导分享到社区 |

### 3. 🧩 **记忆系统（Memosyne 接入）**

- **Episode 记忆**：每 10 轮对话自动提取情景记忆（智能压缩历史，保留最近原文）
- **Semantic 记忆**：语义化提取关键事实（如"用户在金钱和成长间总是偏向成长"）
- **Core 记忆**：用户画像的持久化存储（决策风格、价值观、人生阶段）
- **智能检索**：每轮对话前语义检索 Top-5 相关记忆，动态注入 Prompt

### 4. 🎴 **纠结卡片（Card）**

- **结构化追踪**：每个纠结独立成卡，记录完整对话历史
- **倾向可视化**：实时计算并展示 A/B 选项的倾向百分比（如"创业 60% vs 留下 40%"）
- **自动/手动关闭**：检测决定关键词自动结案，或用户手动标记"已决定/搁置"
- **Insight 生成**：关闭时 LLM 自动提取核心矛盾、价值观信号、担忧类型、行动建议

### 5. 🌍 **纠结社区（Community）**

- **AI 脱敏发布**：卡片关闭后可分享到社区，LLM 自动脱敏敏感信息（隐藏人名、公司名、地点）
- **纠结驱动推荐**：基于当前卡片的核心矛盾，语义匹配推荐相似案例（权重：纠结关键词 > 画像匹配）
- **复盘与满意度**：用户提交决策后满意度（1-10 分）和复盘文本，为他人提供参考
- **互动机制**："我也是"共鸣按钮、浏览数追踪

### 6. 📊 **上下文智能管理**

- **兜底压缩机制**：对话 ≤50 轮全部保留，>50 轮时压缩前期对话为摘要，保留最近 30 轮原文
- **记忆提取优化**：长对话时仅传递"历史摘要 + 最近 10 轮"给记忆提取 API，避免 token 爆炸
- **结构化 JSON 返回**：对话回复强制 JSON 格式（含 message + progress_hint），宽松解析兼容 LLM 格式错误

---

## 🏗️ 技术架构

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.10+ | 后端语言 |
| **FastAPI** | 0.115 | Web 框架（高性能异步） |
| **SQLite** | - | 本地数据库（WAL 模式） |
| **Pydantic** | 2.7 | 数据校验 |
| **Requests** | 2.32 | HTTP 客户端 |
| **Bcrypt** | - | 密码加密 |

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **React** | 19.2 | UI 框架 |
| **React Router** | 7.17 | 路由管理 |
| **Framer Motion** | 12.40 | 动画库 |
| **Lucide React** | 1.18 | 图标库 |
| **Vite** | 8.0 | 构建工具 |

### 外部服务

| 服务 | 用途 | 配置位置 |
|------|------|----------|
| **讯飞 MaaS API** | LLM 推理（DeepSeek V4 Flash / Qwen 4B） | `config.py` |
| **Memosyne API** | 记忆存储与检索 | `config.py` |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- npm 或 yarn

### 1. 克隆项目

```bash
git clone <repository-url>
cd demo
```

### 2. 后端设置

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python database.py

# （可选）填充社区案例种子数据
python -c "from scripts.seed_cases import seed_cases; seed_cases()"

# 启动后端服务
python main.py
# 或使用 uvicorn（支持热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端将运行在 `http://localhost:8000`

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 `http://localhost:5173`

### 4. 配置 API 密钥

编辑 `backend/config.py`，替换为你的实际密钥：

```python
LLM_CONFIG = {
    "api_url": "https://maas-api.cn-huabei-1.xf-yun.com/v2/chat/completions",
    "models": {
        "main": {"id": "your-model-id", "key": "your-api-key"},
        "fast": {"id": "your-fast-model-id", "key": "your-fast-api-key"},
    },
}

MEMORY_CONFIG = {
    "api_url": "http://your-memosyne-host:port",
    "app_id": "your-app-id",
    "repo_id": "your-repo-id",
    "agent_id": "your-agent-id",
}
```

---

## 📡 API 文档

> 📘 **完整 API 文档**：查看 [API_REFERENCE.md](./API_REFERENCE.md) 了解所有接口的详细说明和示例

### 核心 API 概览

| 类别 | 端点 | 说明 |
|------|------|------|
| **认证** | `POST /api/auth/register` | 用户注册 |
|  | `POST /api/auth/login` | 用户登录 |
| **用户** | `GET /api/user/{uid}/profile` | 获取用户画像 |
|  | `PUT /api/user/{uid}/profile` | 更新画像 |
| **卡片** | `POST /api/cards` | 创建纠结卡片 |
|  | `GET /api/cards?uid={uid}` | 获取卡片列表 |
|  | `POST /api/cards/{card_id}/chat` | 对话 |
|  | `PUT /api/cards/{card_id}/close` | 关闭卡片 |
|  | `GET /api/cards/insights?uid={uid}` | Insight 画廊 |
| **记忆** | `GET /api/memories?uid={uid}&type={type}` | 查询记忆 |
|  | `PUT /api/memories/core` | 更新核心档案 |
| **社区** | `GET /api/cases?type={type}` | 案例列表 |
|  | `GET /api/cases/recommendations?card_id={id}` | 推荐相似案例 |
|  | `POST /api/cards/{card_id}/share/preview` | 脱敏预览 |

---

## 📂 目录结构

```
demo/
├── backend/                    # 后端代码
│   ├── clients/               # 外部服务客户端
│   │   ├── llm_client.py     # LLM API 调用（支持 JSON 模式 + 重试）
│   │   ├── memory_client.py  # Memosyne 记忆系统集成
│   │   └── memory_client_local_backup.py  # 本地记忆备份
│   ├── data/                  # 数据目录
│   │   └── app.db            # SQLite 数据库
│   ├── models/                # 数据模型（暂空，使用 dict + Pydantic）
│   ├── prompts/              # Prompt 模板
│   │   ├── base_role.txt     # AI 基础角色设定
│   │   ├── stage_*.txt       # 各阶段 Prompt
│   │   ├── card_extract.txt  # 卡片信息提取
│   │   ├── insight_extract.txt  # Insight 生成
│   │   ├── case_desensitize.txt  # 社区案例脱敏
│   │   ├── value_conflict_check.txt  # 价值观冲突检测
│   │   ├── personality_prompts.py  # GDMS/Maximizer/MBTI 策略
│   │   └── templates.py      # Prompt 加载工具
│   ├── routers/              # API 路由
│   │   ├── auth_router.py    # 注册登录
│   │   ├── user_router.py    # 用户画像
│   │   ├── card_router.py    # 纠结卡片
│   │   ├── memory_router.py  # 记忆管理
│   │   └── case_router.py    # 社区案例
│   ├── scripts/              # 工具脚本
│   │   └── seed_cases.py     # 社区案例种子数据
│   ├── services/             # 业务逻辑层
│   │   ├── card_service.py   # 卡片 CRUD
│   │   ├── case_service.py   # 案例查询、推荐、脱敏、发布
│   │   ├── chat_service.py   # 核心对话编排（阶段切换、记忆注入、倾向计算）
│   │   ├── user_service.py   # 用户管理
│   │   └── context_manager.py  # 上下文压缩（已合并到 chat_service）
│   ├── config.py             # 配置文件（LLM/Memory API）
│   ├── database.py           # 数据库初始化 + 迁移
│   ├── main.py               # FastAPI 应用入口
│   ├── demo_cli.py           # CLI 测试工具
│   └── requirements.txt      # Python 依赖
│
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── api/
│   │   │   └── index.js      # API 调用封装
│   │   ├── components/
│   │   │   └── Toast.jsx     # 通知组件
│   │   ├── hooks/
│   │   │   └── useToast.js   # Toast 钩子
│   │   ├── pages/            # 页面组件
│   │   │   ├── Login.jsx     # 登录页
│   │   │   ├── Onboarding.jsx  # 注册 + 初始化引导
│   │   │   ├── Home.jsx      # 卡片列表首页
│   │   │   ├── NewDilemma.jsx  # 创建新纠结
│   │   │   ├── CardChat.jsx  # 对话页（核心）
│   │   │   ├── Memories.jsx  # 记忆管理页
│   │   │   ├── InsightGallery.jsx  # Insight 画廊
│   │   │   ├── Community.jsx  # 社区案例浏览
│   │   │   └── Settings.jsx  # 设置页（主题切换）
│   │   ├── styles/
│   │   │   └── global.css    # 全局样式（CSS 变量主题系统）
│   │   ├── App.jsx           # 路由配置 + 主题应用
│   │   └── main.jsx          # 入口文件
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
│
├── doc/                       # 文档目录
│   ├── AI个性化决策助手_产品文档.md
│   ├── AI个性化决策助手_产品说明.md
│   ├── GDMS_Implementation_Summary.md  # GDMS 心理学框架实现
│   ├── 心理学框架_深度研究版.md
│   ├── 接口文档_memoryStore_memoryRetrieval.md
│   ├── 记忆系统API接口手册_App开发用.md
│   └── ...（其他设计文档）
│
├── README.md                  # 本文件
└── API_REFERENCE.md          # 完整 API 文档
```

---

## 🧩 核心模块详解

详细的核心模块实现说明请查看 [API_REFERENCE.md](./API_REFERENCE.md) 中的"核心模块详解"部分，包括：

- 对话编排引擎的阶段判断逻辑
- 记忆系统的提取时机和检索策略
- 社区案例系统的推荐算法
- 价值观冲突检测机制
- 上下文压缩策略

---

## ⚙️ 配置说明

### `backend/config.py`

```python
# LLM API 配置（讯飞星火 MaaS 平台）
LLM_CONFIG = {
    "api_url": "https://maas-api.cn-huabei-1.xf-yun.com/v2/chat/completions",
    "models": {
        "main": {"id": "xopdeepseekv4flash", "key": "your-api-key"},
        "fast": {"id": "xop3qwen4b", "key": "your-fast-api-key"},
    },
    "temperature": 0.7,
    "max_tokens": 2048,
}

# Memosyne 记忆系统配置
MEMORY_CONFIG = {
    "api_url": "http://your-memosyne-host:port",
    "app_id": "your-app-id",
    "repo_id": "your-repo-id",
    "agent_id": "decision_agent",
    "retrieval_top_n": 5,
    "retrieval_threshold": 0.25,  # 语义相似度阈值（越低召回越多）
}

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")
```

### 数据库表结构

完整的数据库表结构文档请查看 [API_REFERENCE.md](./API_REFERENCE.md)，包括：

- `users` 表：用户画像
- `cards` 表：纠结卡片
- `messages` 表：对话消息
- `memory_facts` 表：本地记忆备份
- `decision_cases` 表：社区案例

---

## 🛠️ 开发指南

### 本地开发

#### 后端热重载
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端热重载
```bash
cd frontend
npm run dev
```

### 数据库迁移

项目使用 SQLite + 安全迁移机制：

```python
# database.py 中的 _migrate_add_column 函数
# 自动检测并添加缺失的列，已存在则忽略
def _migrate_add_column(conn, table, column, col_type):
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass  # 已存在，忽略
```

**添加新字段步骤：**
1. 在 `database.py` 的 `init_db()` 中添加 `_migrate_add_column()` 调用
2. 重启后端，系统自动执行迁移

### 构建生产版本

#### 后端
```bash
cd backend
# 使用 gunicorn + uvicorn workers
gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 前端
```bash
cd frontend
npm run build
# 生成的静态文件在 frontend/dist/ 目录
```

---

## 📊 性能优化

### 1. 上下文管理
- **兜底阈值**：100 条消息（50 轮）
- **压缩策略**：LLM 总结旧对话 + 保留最近 30 轮原文
- **避免爆炸**：记忆提取时只传"摘要 + 最近 10 轮"

### 2. 记忆系统
- **增量提取**：每 10 轮触发，避免频繁调用
- **智能截断**：长对话只传最近内容给 Memosyne API
- **双重存储**：本地数据库作为 fallback，保证 Core 记忆可用

### 3. LLM 调用
- **JSON 模式**：优先使用 `response_format: json_object`
- **宽松解析**：支持 markdown 包裹、字段重复、尾随逗号等格式错误
- **重试机制**：JSON 解析失败时重试一次 + 增强 Prompt

### 4. 前端优化
- **CSS 变量主题**：动态切换主题色无需重新渲染
- **Framer Motion**：高性能动画库（GPU 加速）
- **懒加载**：路由级代码分割（React Router v7）

---

## 🤝 贡献指南

### Commit 规范
```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构
perf: 性能优化
test: 测试相关
chore: 构建/工具链相关
```

### 提交前检查
- [ ] 代码通过 ESLint（前端）
- [ ] 后端 API 通过手动测试
- [ ] 更新相关文档（README / API_REFERENCE）

---

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- **讯飞星火 MaaS 平台**：提供高性能 LLM 推理服务
- **Memosyne 团队**：提供企业级记忆系统
- **FastAPI 社区**：提供优秀的现代 Python Web 框架
- **React Router 团队**：提供强大的前端路由解决方案

---

## 📮 联系方式

- **项目负责人**：科大讯飞核心研发平台
- **技术支持**：[提交 Issue](https://github.com/your-repo/issues)
- **产品文档**：查看 [doc/](./doc/) 目录

---

**Made with ❤️ by 科大讯飞核心研发平台**
