# 聚合搜索 API 接口文档

## 📋 基本信息

**API 名称**：聚合搜索（AggSearch）  
**功能**：联网搜索知识库，返回相关文档和内容  
**版本**：v1.0  
**环境要求**：需要办公网访问权限

---

## 🔑 配置信息

```python
AGG_SEARCH_CONFIG = {
    "app_id": "187837596",
    "api_key": "79f2820e-2ada-45ba-b193-596bc014ed9d",
    "business": "knowledge_base",
    "host": "http://dx-cbm-ocp-agg-search-inner.xf-yun.com/search",
    "extra_info": '{"domain":"generalv4","env":"dx-v4-0"}',
    "timeout": 3000,
    "high_light": True
}
```

**字段说明**：
- `app_id`: 应用标识符
- `api_key`: API密钥（用于生成token，当前示例中未使用）
- `business`: 业务类型，固定为 `knowledge_base`
- `host`: API 请求地址
- `extra_info`: 额外配置信息（JSON字符串）
- `timeout`: 请求超时时间（毫秒）
- `high_light`: 是否启用高亮显示

---

## 🌐 接口定义

### 请求信息

**请求方法**：`POST`  
**请求地址**：`http://dx-cbm-ocp-agg-search-inner.xf-yun.com/search`  
**Content-Type**：`application/json`

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `pipeline_name` | string | 是 | 管道名称（如 `pl_map_agg_search`） |
| `appId` | string | 是 | 应用ID（同配置中的 app_id） |
| `name` | string | 是 | 搜索查询关键词 |
| `append` | string | 是 | 附加数据（JSON字符串，包含 sid 和 caller） |
| `uId` | string | 是 | 用户ID（可与 appId 相同） |
| `extraInfo` | string | 是 | 额外信息（JSON字符串，domain + env） |
| `limit` | int | 是 | 返回结果数量上限 |
| `sid` | string | 是 | 会话ID（**使用时间戳**，如 `str(int(time.time() * 1000))`） |
| `open_rerank` | bool | 是 | 是否开启重排序（建议 `true`） |
| `disable_highlight` | bool | 是 | 是否禁用高亮（`false` = 启用） |
| `disable_crawler` | bool | 是 | 是否禁用爬虫（建议 `true`） |
| `full_text` | bool | 是 | 是否全文搜索（建议 `true`） |
| `business` | string | 是 | 业务类型（`knowledge_base`） |
| `sites` | array | 否 | 限定搜索的站点列表 |

**请求体示例**：
```json
{
  "pipeline_name": "pl_map_agg_search",
  "appId": "187837596",
  "name": "Python 异步编程教程",
  "append": "{\"sid\":\"1704988800000\",\"caller\":\"187837596\"}",
  "uId": "187837596",
  "extraInfo": "{\"domain\":\"generalv4\",\"env\":\"dx-v4-0\"}",
  "limit": 10,
  "sid": "1704988800000",
  "open_rerank": true,
  "disable_highlight": false,
  "disable_crawler": true,
  "full_text": true,
  "business": "knowledge_base",
  "sites": []
}
```

**⚠️ 重要**：`sid` 必须使用**时间戳**（毫秒级），如 `"1704988800000"`

---

## 📤 响应格式

### 成功响应

**HTTP 状态码**：`200 OK`

**响应体结构**：
```json
{
  "success": true,
  "errCode": "0",
  "errMsg": "",
  "data": {
    "documents": [
      {
        "name": "文档标题",
        "summary": "文档摘要",
        "content": "完整内容或片段",
        "url": "https://example.com/article",
        "source": "来源站点",
        "frScore": 0.95,
        "publishedDate": "2025-01-15"
      }
    ]
  }
}
```

**字段说明**：
- `success`: 请求是否成功
- `errCode`: 错误码（`"0"` 表示成功）
- `errMsg`: 错误信息
- `data.documents`: 文档列表
  - `name`: 文档标题
  - `summary`: 文档摘要（通常是高亮后的关键片段）
  - `content`: 完整内容或长片段
  - `url`: 原始链接
  - `source`: 来源（如网站名称）
  - `frScore`: 相关性得分（0-1）
  - `publishedDate`: 发布日期

### 失败响应

**HTTP 状态码**：`200 OK`（业务错误码在响应体中）

```json
{
  "success": false,
  "errCode": "10001",
  "errMsg": "参数错误",
  "data": null
}
```

**常见错误码**：
- `10001`: 参数错误
- `10002`: 认证失败
- `10003`: 查询超时
- `10004`: 未找到结果

---

## 🐍 Python 调用示例

### 1. 基础封装类

```python
import json
import time
import requests
from typing import List, Dict, Optional

class AggSearchClient:
    def __init__(self, config: Dict):
        self.app_id = config["app_id"]
        self.api_key = config["api_key"]
        self.host = config["host"]
        self.business = config["business"]
        self.extra_info = config["extra_info"]
        self.timeout = config["timeout"] / 1000  # 转换为秒
        self.high_light = config["high_light"]
    
    def search(
        self, 
        query: str, 
        sid: Optional[str] = None,
        limit: int = 10,
        pipeline_name: str = "pl_map_agg_search",
        sites: Optional[List[str]] = None
    ) -> tuple[List[Dict], str]:
        """
        执行聚合搜索
        
        Args:
            query: 搜索关键词
            sid: 会话ID（如不提供则自动生成时间戳）
            limit: 返回结果数量上限
            pipeline_name: 管道名称
            sites: 限定搜索的站点列表
        
        Returns:
            (搜索结果列表, 会话ID)
        
        Raises:
            Exception: 请求失败或业务错误
        """
        # 生成时间戳 sid（毫秒级）
        if sid is None:
            sid = str(int(time.time() * 1000))
        
        # 构建 append 数据
        append_data = {
            "sid": sid,
            "caller": self.app_id
        }
        
        # 构建请求体
        body = {
            "pipeline_name": pipeline_name,
            "appId": self.app_id,
            "name": query,
            "append": json.dumps(append_data),
            "uId": self.app_id,
            "extraInfo": self.extra_info,
            "limit": limit,
            "sid": sid,
            "open_rerank": True,
            "disable_highlight": not self.high_light,
            "disable_crawler": True,
            "full_text": True,
            "business": self.business,
            "sites": sites or []
        }
        
        # 发送请求
        try:
            response = requests.post(
                self.host,
                json=body,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP 请求失败: {str(e)}")
        
        # 解析响应
        result = response.json()
        
        if not result.get("success") or result.get("errCode") != "0":
            raise Exception(
                f"聚合搜索失败 - errCode: {result.get('errCode')}, "
                f"errMsg: {result.get('errMsg')}"
            )
        
        # 提取文档列表
        documents = result.get("data", {}).get("documents", [])
        
        # 格式化结果
        results = []
        for doc in documents:
            results.append({
                "title": doc.get("name", ""),
                "summary": doc.get("summary", ""),
                "content": doc.get("content", ""),
                "url": doc.get("url", ""),
                "source": doc.get("source", ""),
                "score": doc.get("frScore", 0.0),
                "published_date": doc.get("publishedDate", "")
            })
        
        return results, sid
```

### 2. 使用示例

```python
# 初始化客户端
config = {
    "app_id": "187837596",
    "api_key": "79f2820e-2ada-45ba-b193-596bc014ed9d",
    "business": "knowledge_base",
    "host": "http://dx-cbm-ocp-agg-search-inner.xf-yun.com/search",
    "extra_info": '{"domain":"generalv4","env":"dx-v4-0"}',
    "timeout": 3000,
    "high_light": True
}

client = AggSearchClient(config)

# 执行搜索（sid 自动生成时间戳）
try:
    results, session_id = client.search(
        query="Python 异步编程最佳实践",
        limit=5
    )
    
    print(f"会话ID: {session_id}")  # 输出：1704988800000（时间戳）
    print(f"找到 {len(results)} 条结果：")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   来源：{result['source']}")
        print(f"   摘要：{result['summary'][:100]}...")
        print(f"   链接：{result['url']}")
        print(f"   得分：{result['score']}")
        
except Exception as e:
    print(f"搜索失败：{str(e)}")

# 或者手动指定 sid（也必须是时间戳格式）
import time
custom_sid = str(int(time.time() * 1000))
results, _ = client.search(
    query="另一个查询",
    sid=custom_sid
)
```
```

---

## 🎯 在"不纠结"项目中的应用场景

### 1. 决策信息补充

**场景**：用户在做产品对比决策时，需要最新的产品评测信息

**示例**：
```python
# 用户纠结买哪款手机
query = "iPhone 15 Pro vs 小米 14 对比评测"
results, _ = client.search(query, limit=3)  # sid 自动生成

# 提取关键信息后整合到对话中
context = "\n\n".join([
    f"【{r['source']}】{r['summary']}" 
    for r in results[:3]
])

system_prompt += f"\n\n【最新信息】\n{context}"
```

### 2. Insight 生成增强

**场景**：生成决策复盘时，引用相关理论或案例

**示例**：
```python
# 基于用户的决策类型搜索相关理论
if decision_type == "career":
    query = "职业转型决策 心理学研究"
    results, _ = client.search(query, limit=2)
    
    # 在 Insight 中引用
    insight += f"\n\n相关研究：{results[0]['summary']}"
```

### 3. 实时信息验证

**场景**：AI建议前先搜索最新信息验证

**示例**：
```python
# 用户问："现在买房合适吗？"
query = "2025年中国房地产市场政策趋势"
results, _ = client.search(query, limit=3)

# 基于最新信息给出建议
latest_info = results[0]['summary']
```

---

## ⚠️ 注意事项

### 1. 网络限制
- ⚠️ **需要办公网访问权限**
- 内网环境无法直接调用
- 解决方案：
  - 通过跳板机（SSH隧道）访问
  - 部署在办公网环境的服务器上
  - 使用代理服务器

**SSH 跳板机示例**：
```bash
# 连接跳板机
ssh awmao:Wa!!&@ddYtc321@172.16.154.251

# 或在代码中通过跳板机转发请求
ssh -L 8080:dx-cbm-ocp-agg-search-inner.xf-yun.com:80 awmao@172.16.154.251
# 然后请求 http://localhost:8080/search
```

### 2. 性能考虑
- 默认超时 3 秒，可能不够
- 建议异步调用，避免阻塞主流程
- 搜索结果缓存（相同query在短时间内不重复请求）

### 3. 结果质量
- `frScore` 相关性得分：建议只取 > 0.7 的结果
- `summary` 通常比 `content` 更精炼，优先使用
- 开启 `high_light` 可以更容易定位关键信息

### 4. 成本控制
- 每次搜索消耗一定资源
- 建议：
  - 限制 `limit` 参数（5-10条即可）
  - 避免高频调用
  - 用户主动触发 vs AI自动触发（需权衡）

---

## 📝 完整集成示例（FastAPI）

```python
# backend/clients/agg_search_client.py

import json
import time
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AggSearchClient:
    def __init__(self, config: Dict):
        self.app_id = config["app_id"]
        self.host = config["host"]
        self.business = config["business"]
        self.extra_info = config["extra_info"]
        self.timeout = config["timeout"] / 1000
        self.high_light = config["high_light"]
    
    def search(
        self, 
        query: str, 
        sid: Optional[str] = None,
        limit: int = 10,
        pipeline_name: str = "pl_map_agg_search"
    ) -> List[Dict]:
        """执行聚合搜索"""
        # 生成时间戳 sid（毫秒级）
        if sid is None:
            sid = str(int(time.time() * 1000))
        
        append_data = {"sid": sid, "caller": self.app_id}
        
        body = {
            "pipeline_name": pipeline_name,
            "appId": self.app_id,
            "name": query,
            "append": json.dumps(append_data),
            "uId": self.app_id,
            "extraInfo": self.extra_info,
            "limit": limit,
            "sid": sid,
            "open_rerank": True,
            "disable_highlight": not self.high_light,
            "disable_crawler": True,
            "full_text": True,
            "business": self.business,
            "sites": []
        }
        
        try:
            response = requests.post(
                self.host,
                json=body,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get("success") or result.get("errCode") != "0":
                logger.error(f"AggSearch 失败: {result.get('errMsg')}")
                return []
            
            documents = result.get("data", {}).get("documents", [])
            
            # 只返回高质量结果
            return [
                {
                    "title": doc.get("name", ""),
                    "summary": doc.get("summary", ""),
                    "url": doc.get("url", ""),
                    "source": doc.get("source", ""),
                    "score": doc.get("frScore", 0.0)
                }
                for doc in documents
                if doc.get("frScore", 0) > 0.7  # 过滤低质量结果
            ]
        
        except Exception as e:
            logger.error(f"AggSearch 异常: {str(e)}")
            return []

# 全局实例
agg_search_client = None

def get_agg_search_client() -> Optional[AggSearchClient]:
    """获取聚合搜索客户端（单例）"""
    global agg_search_client
    if agg_search_client is None:
        try:
            config = {
                "app_id": "187837596",
                "api_key": "79f2820e-2ada-45ba-b193-596bc014ed9d",
                "business": "knowledge_base",
                "host": "http://dx-cbm-ocp-agg-search-inner.xf-yun.com/search",
                "extra_info": '{"domain":"generalv4","env":"dx-v4-0"}',
                "timeout": 3000,
                "high_light": True
            }
            agg_search_client = AggSearchClient(config)
        except Exception as e:
            logger.warning(f"AggSearch 客户端初始化失败: {str(e)}")
            return None
    return agg_search_client
```

---

## 🚀 后续集成步骤（可选）

1. **创建客户端文件**：`backend/clients/agg_search_client.py`
2. **在对话服务中集成**：`backend/services/chat_service.py`
3. **添加用户触发按钮**：前端卡片详情页增加"搜索相关信息"
4. **异步处理**：使用 `BackgroundTasks` 避免阻塞

---

**文档版本**：v1.0  
**最后更新**：2025-06-XX  
**维护者**：@xtyu9

---

## AggSearch 跳板机访问补充

AggSearch 的 host 是办公网/内网地址，本地直连可能超时。可以通过跳板机连通：

```bash
ssh awmao@172.16.154.251
```

密码不要写入文档或代码仓库，连接时按提示输入。

如需在本机调用 AggSearch，可以建立本地端口转发：

```bash
ssh -L 8080:dx-cbm-ocp-agg-search-inner.xf-yun.com:80 awmao@172.16.154.251
```

隧道建立后，本地请求地址改为：

```text
http://localhost:8080/search
```

注意：
- 请求方法仍然是 `POST`
- `Content-Type` 仍然是 `application/json`
- 顶层 `sid` 和 `append.sid` 必须一致
- `sid` 必须使用毫秒级 timestamp，例如 `str(int(time.time() * 1000))`
