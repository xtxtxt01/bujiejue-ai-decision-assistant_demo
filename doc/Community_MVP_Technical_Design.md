# 纠结社区 MVP 技术设计文档

## 📋 文档说明

**版本**：v1.0 (极简 MVP)  
**目标**：用最小成本验证"看相似案例"的核心价值  
**工期**：3-4天  
**状态**：设计阶段

---

## 🎯 核心范围

### ✅ 做什么

1. **案例浏览** - 按类型筛选查看预置案例
2. **案例详情** - 展示完整的决策过程和结果
3. **轻量互动** - "我也是"共鸣标记
4. **数据持久化** - 案例存储和查询

### ❌ 不做什么（延后到V2）

1. ❌ 用户贡献案例（先用预置内容）
2. ❌ 对话中RAG引入（先独立浏览）
3. ❌ 复杂匹配算法（先按类型筛选）
4. ❌ 审核系统（预置内容无需审核）
5. ❌ 评论、私信、关注等社交功能

---

## 🗄️ 数据库设计

### 新增表：decision_cases

```sql
CREATE TABLE IF NOT EXISTS decision_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 基本信息
    case_type VARCHAR(50) NOT NULL,        -- 纠结类型：career/relationship/lifestyle/finance/education
    title TEXT NOT NULL,                   -- 案例标题（用于列表显示）
    
    -- 决策结构（核心内容）
    background TEXT NOT NULL,              -- 脱敏背景（如：互联网3年 | 薪资+30%）
    core_conflict TEXT NOT NULL,           -- 核心矛盾（如：成长 vs 稳定）
    duration_days INTEGER NOT NULL,        -- 纠结时长（天）
    final_choice TEXT NOT NULL,            -- 最终选择
    turning_point TEXT NOT NULL,           -- 决策转折点
    
    -- 结果验证（必须字段）
    retrospect TEXT NOT NULL,              -- 事后回顾
    retrospect_score INTEGER NOT NULL,     -- 满意度评分 1-10
    retrospect_months INTEGER DEFAULT 3,   -- 回顾时间（几个月后）
    
    -- 匹配维度（用于后续推荐）
    decision_style VARCHAR(50),            -- 决策风格：rational/intuitive/dependent/avoidant/spontaneous
    life_stage VARCHAR(50),                -- 人生阶段：student/early_career/mid_career等
    tags TEXT,                             -- 标签（逗号分隔，如：跳槽,成长,薪资）
    
    -- 互动数据
    empathy_count INTEGER DEFAULT 0,       -- "我也是"数量
    view_count INTEGER DEFAULT 0,          -- 浏览次数
    
    -- 元数据
    is_featured BOOLEAN DEFAULT 0,         -- 是否精选（运营标记）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    CHECK (retrospect_score >= 1 AND retrospect_score <= 10),
    CHECK (duration_days > 0)
);

-- 创建索引（提升查询性能）
CREATE INDEX IF NOT EXISTS idx_case_type ON decision_cases(case_type);
CREATE INDEX IF NOT EXISTS idx_decision_style ON decision_cases(decision_style);
CREATE INDEX IF NOT EXISTS idx_created_at ON decision_cases(created_at DESC);
```

### 字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `case_type` | 枚举 | 纠结类型 | `career`, `relationship`, `lifestyle`, `finance`, `education` |
| `title` | 文本 | 简短标题 | "跳槽 vs 留下：成长空间的抉择" |
| `background` | 文本 | 脱敏背景 | "互联网3年 \| 薪资+30% \| 加班更多" |
| `core_conflict` | 文本 | 核心矛盾 | "成长空间 vs 稳定性" |
| `duration_days` | 整数 | 纠结天数 | `21` |
| `final_choice` | 文本 | 最终决定 | "选择跳槽" |
| `turning_point` | 文本 | 转折点 | "想通了哪个更后悔" |
| `retrospect` | 文本 | 事后回顾 | "不后悔，虽然前3个月很累..." |
| `retrospect_score` | 1-10 | 满意度 | `8` |
| `decision_style` | 枚举 | 决策风格 | `rational` |
| `life_stage` | 枚举 | 人生阶段 | `early_career` |
| `tags` | CSV | 标签 | "跳槽,成长,薪资" |

---

## 🎨 前端设计

### 页面结构

```
/community
├── 顶部导航栏（返回 + 标题）
├── 分类筛选栏（全部/工作/感情/生活/消费/学业）
└── 案例列表
    └── 案例卡片
        ├── 标题
        ├── 背景标签
        ├── 核心矛盾
        ├── 纠结时长
        ├── 最终选择
        ├── 转折点（收起/展开）
        ├── 事后回顾（收起/展开）
        └── 互动按钮（我也是 + 数量）
```

### 组件层级

```
Community (页面)
├── Navbar (导航栏)
├── FilterTabs (筛选栏)
└── CaseList (列表容器)
    └── CaseCard (案例卡片) × N
        ├── CaseHeader (标题+标签)
        ├── CaseBody (核心内容)
        │   ├── ConflictSection (矛盾)
        │   ├── ChoiceSection (选择)
        │   ├── TurningPointSection (转折，可展开)
        │   └── RetrospectSection (回顾，可展开)
        └── CaseFooter (互动)
```

### 状态管理

```typescript
interface CommunityState {
  cases: Case[];              // 案例列表
  filter: CaseType | 'all';   // 当前筛选
  loading: boolean;           // 加载状态
  error: string | null;       // 错误信息
}

interface Case {
  id: number;
  case_type: string;
  title: string;
  background: string;
  core_conflict: string;
  duration_days: number;
  final_choice: string;
  turning_point: string;
  retrospect: string;
  retrospect_score: number;
  retrospect_months: number;
  decision_style: string;
  life_stage: string;
  tags: string;
  empathy_count: number;
  view_count: number;
  is_featured: boolean;
  created_at: string;
}
```

### 交互细节

1. **案例卡片**
   - 默认收起"转折点"和"事后回顾"（节省空间）
   - 点击"展开"查看完整内容
   - 点击"我也是"按钮增加共鸣数（乐观更新）

2. **筛选切换**
   - 切换时显示加载状态
   - 无数据时显示空状态提示

3. **性能优化**
   - 列表虚拟滚动（如果案例 > 50个）
   - 图片懒加载（虽然MVP没图片，但预留）

---

## 🔌 API 设计

### 1. 获取案例列表

**接口**：`GET /api/cases`

**Query 参数**：
- `type` (可选): 筛选类型，`all` | `career` | `relationship` | `lifestyle` | `finance` | `education`
- `limit` (可选): 返回数量，默认 50
- `offset` (可选): 分页偏移，默认 0

**响应**：
```json
{
  "success": true,
  "cases": [
    {
      "id": 1,
      "case_type": "career",
      "title": "跳槽 vs 留下：成长空间的抉择",
      "background": "互联网3年 | 薪资+30% | 加班更多",
      "core_conflict": "成长空间 vs 稳定性",
      "duration_days": 21,
      "final_choice": "选择跳槽",
      "turning_point": "想通了\"适应期不舒服\"和\"一直待着不成长\"哪个更后悔",
      "retrospect": "不后悔，虽然前3个月很累，但学到了很多新东西",
      "retrospect_score": 8,
      "retrospect_months": 3,
      "decision_style": "rational",
      "life_stage": "early_career",
      "tags": "跳槽,成长,薪资",
      "empathy_count": 127,
      "view_count": 456,
      "is_featured": true,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "has_more": false
}
```

**错误响应**：
```json
{
  "success": false,
  "error": "Invalid case type"
}
```

---

### 2. 增加共鸣数

**接口**：`POST /api/cases/{case_id}/empathy`

**路径参数**：
- `case_id`: 案例ID

**请求头**：
```
Content-Type: application/json
```

**请求体**：
```json
{}
```

**响应**：
```json
{
  "success": true,
  "empathy_count": 128
}
```

**错误响应**：
```json
{
  "success": false,
  "error": "Case not found"
}
```

---

### 3. 增加浏览数（后台自动调用）

**接口**：`POST /api/cases/{case_id}/view`

**说明**：前端进入案例详情页时自动调用（如果后续有详情页）

---

## 🏗️ 后端架构

### 文件结构

```
backend/
├── routers/
│   └── case_router.py          # 案例相关路由
├── services/
│   └── case_service.py         # 案例业务逻辑
├── models/
│   └── case_model.py           # 案例数据模型（可选）
├── database.py                 # 数据库连接
└── main.py                     # 注册路由
```

### 代码结构

```python
# routers/case_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from ..services.case_service import CaseService
from ..database import get_db

router = APIRouter(prefix="/api/cases", tags=["cases"])

@router.get("")
async def get_cases(
    type: Optional[str] = Query("all", regex="^(all|career|relationship|lifestyle|finance|education)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db = Depends(get_db)
):
    """获取案例列表"""
    service = CaseService(db)
    cases = service.get_cases(case_type=type, limit=limit, offset=offset)
    total = service.count_cases(case_type=type)
    
    return {
        "success": True,
        "cases": cases,
        "total": total,
        "has_more": offset + len(cases) < total
    }

@router.post("/{case_id}/empathy")
async def add_empathy(
    case_id: int,
    db = Depends(get_db)
):
    """增加共鸣数"""
    service = CaseService(db)
    new_count = service.add_empathy(case_id)
    
    if new_count is None:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return {
        "success": True,
        "empathy_count": new_count
    }
```

```python
# services/case_service.py
from typing import Optional, List, Dict, Any
import sqlite3

class CaseService:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
    
    def get_cases(
        self, 
        case_type: str = "all",
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取案例列表"""
        query = """
            SELECT * FROM decision_cases
            WHERE 1=1
        """
        params = []
        
        if case_type != "all":
            query += " AND case_type = ?"
            params.append(case_type)
        
        query += " ORDER BY is_featured DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = self.db.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def count_cases(self, case_type: str = "all") -> int:
        """统计案例数量"""
        query = "SELECT COUNT(*) FROM decision_cases WHERE 1=1"
        params = []
        
        if case_type != "all":
            query += " AND case_type = ?"
            params.append(case_type)
        
        cursor = self.db.execute(query, params)
        return cursor.fetchone()[0]
    
    def add_empathy(self, case_id: int) -> Optional[int]:
        """增加共鸣数，返回新的计数"""
        try:
            cursor = self.db.execute(
                "UPDATE decision_cases SET empathy_count = empathy_count + 1 WHERE id = ?",
                (case_id,)
            )
            
            if cursor.rowcount == 0:
                return None
            
            self.db.commit()
            
            # 获取新的计数
            cursor = self.db.execute(
                "SELECT empathy_count FROM decision_cases WHERE id = ?",
                (case_id,)
            )
            result = cursor.fetchone()
            
            return result[0] if result else None
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def add_view(self, case_id: int) -> bool:
        """增加浏览数"""
        try:
            cursor = self.db.execute(
                "UPDATE decision_cases SET view_count = view_count + 1 WHERE id = ?",
                (case_id,)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
            self.db.rollback()
            return False
```

---

## 🧪 测试策略

### 单元测试

```python
# tests/test_case_service.py

import pytest
from backend.services.case_service import CaseService

def test_get_cases_all(test_db):
    """测试获取全部案例"""
    service = CaseService(test_db)
    cases = service.get_cases(case_type="all", limit=10, offset=0)
    assert isinstance(cases, list)
    assert len(cases) <= 10

def test_get_cases_filtered(test_db):
    """测试按类型筛选"""
    service = CaseService(test_db)
    cases = service.get_cases(case_type="career", limit=10, offset=0)
    assert all(c['case_type'] == 'career' for c in cases)

def test_add_empathy(test_db):
    """测试增加共鸣数"""
    service = CaseService(test_db)
    initial_count = service.get_cases()[0]['empathy_count']
    new_count = service.add_empathy(1)
    assert new_count == initial_count + 1

def test_add_empathy_invalid_id(test_db):
    """测试无效ID"""
    service = CaseService(test_db)
    result = service.add_empathy(99999)
    assert result is None
```

### 集成测试

```python
# tests/test_case_api.py

from fastapi.testclient import TestClient

def test_get_cases_api(client: TestClient):
    """测试获取案例API"""
    response = client.get("/api/cases")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "cases" in data

def test_add_empathy_api(client: TestClient):
    """测试共鸣API"""
    response = client.post("/api/cases/1/empathy")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "empathy_count" in data
```

---

## 🚀 部署与迁移

### 数据库迁移

```python
# backend/migrations/add_decision_cases.py

def upgrade(db):
    """创建 decision_cases 表"""
    db.execute("""
        CREATE TABLE IF NOT EXISTS decision_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_type VARCHAR(50) NOT NULL,
            title TEXT NOT NULL,
            background TEXT NOT NULL,
            core_conflict TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            final_choice TEXT NOT NULL,
            turning_point TEXT NOT NULL,
            retrospect TEXT NOT NULL,
            retrospect_score INTEGER NOT NULL,
            retrospect_months INTEGER DEFAULT 3,
            decision_style VARCHAR(50),
            life_stage VARCHAR(50),
            tags TEXT,
            empathy_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            is_featured BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (retrospect_score >= 1 AND retrospect_score <= 10),
            CHECK (duration_days > 0)
        )
    """)
    
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_case_type 
        ON decision_cases(case_type)
    """)
    
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_decision_style 
        ON decision_cases(decision_style)
    """)
    
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at 
        ON decision_cases(created_at DESC)
    """)
    
    db.commit()

def downgrade(db):
    """回滚"""
    db.execute("DROP TABLE IF EXISTS decision_cases")
    db.commit()
```

### 预置数据导入

```bash
# 导入预置案例
python -m backend.scripts.seed_cases
```

---

## 📊 性能指标

### 性能目标

| 指标 | 目标 | 说明 |
|------|------|------|
| API响应时间 | < 200ms | 99th percentile |
| 前端首屏加载 | < 1s | 包含数据请求 |
| 数据库查询 | < 50ms | 单次查询 |
| 并发处理 | 100 req/s | 峰值 |

### 优化手段

1. **数据库**
   - 在常用字段上建索引
   - 限制单次查询数量（max 100）
   - 使用 COUNT 缓存（如果案例总数不常变）

2. **前端**
   - 列表虚拟滚动（react-window）
   - 案例卡片懒渲染
   - 乐观更新（点赞立即生效）

3. **缓存**
   - 考虑加 Redis（V2）
   - 前端缓存筛选结果（5分钟）

---

## 🔒 安全考虑

### 输入验证

1. **API 参数**
   - `type`: 枚举验证（FastAPI Query regex）
   - `limit`: 范围验证（1-100）
   - `offset`: 非负整数
   - `case_id`: 整数且存在性检查

2. **SQL 注入**
   - 使用参数化查询（避免字符串拼接）
   - 所有用户输入都通过 `?` 占位符

### 速率限制

```python
# 防止刷共鸣数
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/{case_id}/empathy")
@limiter.limit("10/minute")  # 每分钟最多10次
async def add_empathy(...):
    ...
```

---

## 📈 监控与日志

### 关键指标

1. **业务指标**
   - 案例浏览数 PV/UV
   - 共鸣点击率
   - 各类型案例占比

2. **技术指标**
   - API 响应时间
   - 错误率
   - 数据库查询性能

### 日志规范

```python
import logging

logger = logging.getLogger(__name__)

# INFO: 业务操作
logger.info(f"User {uid} viewed case {case_id}")
logger.info(f"Case {case_id} empathy count increased to {count}")

# WARNING: 异常但可恢复
logger.warning(f"Case {case_id} not found for empathy")

# ERROR: 系统错误
logger.error(f"Database error: {str(e)}", exc_info=True)
```

---

## ✅ 实施检查清单

### 后端

- [ ] 创建数据库表（迁移脚本）
- [ ] 实现 CaseService（业务逻辑）
- [ ] 实现 case_router（API路由）
- [ ] 注册路由到 main.py
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 导入预置案例

### 前端

- [ ] 创建 Community 页面
- [ ] 实现 FilterTabs 组件
- [ ] 实现 CaseCard 组件
- [ ] 实现 CaseList 组件
- [ ] 添加路由配置
- [ ] 添加导航入口（底部Tab或Home页入口）
- [ ] 测试交互流程

### 联调

- [ ] 前后端接口联调
- [ ] 测试筛选功能
- [ ] 测试共鸣功能
- [ ] 测试空状态
- [ ] 测试错误处理
- [ ] 性能测试

### 文档

- [ ] 更新 README（新增社区功能）
- [ ] 更新 API 文档
- [ ] 编写预置案例文档

---

## 🎓 技术债务记录

### 已知限制（MVP阶段可接受）

1. **无分页** - 目前只取前50条，够用但不可扩展
2. **无缓存** - 每次请求都查数据库
3. **无搜索** - 只能按类型筛选
4. **无收藏** - 用户无法保存喜欢的案例
5. **无详情页** - 卡片内容较多，展开/收起体验一般

### 后续优化方向（V2）

1. **分页加载** - 无限滚动或分页器
2. **Redis缓存** - 热门案例缓存
3. **全文搜索** - SQLite FTS5 或 Elasticsearch
4. **收藏功能** - 用户个人参考库
5. **详情页** - 独立页面展示完整案例
6. **匹配推荐** - 基于用户画像的个性化推荐

---

## 🔄 版本规划

### V1.0 - 极简MVP（当前）
- ✅ 浏览预置案例
- ✅ 按类型筛选
- ✅ "我也是"共鸣

### V1.5 - 增强版（1-2周后）
- 用户贡献案例
- AI 脱敏
- 收藏功能

### V2.0 - 完整版（1个月后）
- 个性化推荐
- 对话中 RAG 引入
- 搜索功能

---

**文档完成时间**：2025-06-XX  
**审核状态**：待审核  
**下一步**：编写预置案例文档
