"""
Memosyne 记忆系统客户端 — 接入真实的 Memosyne API

核心功能：
1. extract_and_store_memories: 每轮对话后，调用 memoryStore 自动提取并存储记忆
2. retrieve_memories: 对话前，调用 memoryRetrieval 语义检索相关记忆
3. build_memory_context: 构建完整的记忆上下文（用户画像 + 历史记忆）

API 接口：
- memoryStore: 自动提取对话中的记忆（episode + semantic）
- memoryRetrieval: 根据当前输入语义检索相关记忆
"""
import requests
from datetime import datetime
from database import get_db
from config import MEMORY_CONFIG


def extract_and_store_memories(uid: str, card_id: str, messages: list[dict]) -> list[dict]:
    """
    从对话消息中提取记忆并存储到 Memosyne

    使用 memoryStore 接口，系统会自动提取 episode 和 semantic 记忆

    Args:
        uid: 用户ID
        card_id: 纠结卡片ID（用于关联记忆来源）
        messages: 对话消息列表，格式 [{"role": "user/assistant", "content": "..."}]

    Returns:
        提取的记忆列表（如果 API 返回详细信息）
    """
    url = f"{MEMORY_CONFIG['api_url']}/v1/s/memosyne/memoryStore"

    payload = {
        "appId": MEMORY_CONFIG["app_id"],
        "uid": uid,
        "agentId": MEMORY_CONFIG["agent_id"],
        "repoId": MEMORY_CONFIG["repo_id"],
        "memoryType": ["episode", "semantic"],  # 同时提取情景记忆和语义记忆
        "messages": messages
    }

    try:
        # 注意：memoryStore 处理较慢，不设置超时限制
        resp = requests.post(url, json=payload)
        data = resp.json()

        if data.get("code") == 0:
            # 存储成功，返回空列表（memoryStore 不返回提取的具体内容）
            return []
        else:
            print(f"[Memory] memoryStore failed: code={data.get('code')}, msg={data.get('message')}")
            return []
    except Exception as e:
        print(f"[Memory] memoryStore error: {e}")
        return []


def retrieve_memories(uid: str, query: str, top_n: int = 5) -> list[str]:
    """
    根据用户输入语义检索相关记忆

    使用 memoryRetrieval 接口，返回格式化的记忆文本列表

    Args:
        uid: 用户ID
        query: 用户当前输入
        top_n: 返回记忆条数

    Returns:
        相关记忆的文本列表（已格式化，可直接拼入 prompt）
    """
    url = f"{MEMORY_CONFIG['api_url']}/v1/s/memosyne/memoryRetrieval"

    payload = {
        "appId": MEMORY_CONFIG["app_id"],
        "uid": uid,
        "agentId": MEMORY_CONFIG["agent_id"],
        "repoId": MEMORY_CONFIG["repo_id"],
        "retrievalMode": "quickRetrieval",
        "messages": [{"role": "user", "content": query}],
        "memoryType": ["episode", "semantic", "core"],  # 检索所有类型
        "topN": top_n,
        "threshold": MEMORY_CONFIG["retrieval_threshold"],
        "getBasicInfo": True  # 同时返回用户基础信息
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()

        if data.get("code") == 0:
            result = data.get("data", {}).get("result", [])
            # result 是格式化好的记忆文本列表，可以直接使用
            return result
        else:
            print(f"[Memory] memoryRetrieval failed: code={data.get('code')}")
            return []
    except Exception as e:
        print(f"[Memory] memoryRetrieval error: {e}")
        return []


def upsert_core_memory(uid: str, core_items: list[dict]) -> bool:
    """
    手动写入 core 记忆（用户画像的持久化关键事实）

    Args:
        uid: 用户ID
        core_items: core 记忆列表，每项格式 {"content": "...", "tags": [...]}

    Returns:
        True if success, False otherwise
    """
    if not core_items:
        return False

    url = f"{MEMORY_CONFIG['api_url']}/v1/s/memosyne/memoryUpsert"

    # core 字段格式：map[string][]CoreContent，key 为分类名，value 为该分类下的记忆数组
    payload = {
        "appId": MEMORY_CONFIG["app_id"],
        "uid": uid,
        "agentId": MEMORY_CONFIG["agent_id"],
        "repoId": MEMORY_CONFIG["repo_id"],
        "memoryType": "core",
        "core": {"profile": core_items},
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            return True
        else:
            print(f"[Memory] upsert_core_memory failed: code={data.get('code')}, msg={data.get('message')}")
            return False
    except Exception as e:
        print(f"[Memory] upsert_core_memory error: {e}")
        return False


def get_user_profile_memory(uid: str) -> str:
    """
    获取用户画像的文本描述（从本地 users 表读取）

    用户画像存储在本地数据库，不通过记忆系统 API

    Args:
        uid: 用户ID

    Returns:
        用户画像的格式化文本
    """
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
    conn.close()

    if not row:
        return ""

    parts = []
    if row["mbti"]:
        parts.append(f"MBTI类型：{row['mbti']}")
    if row["decision_style"]:
        style_map = {
            "rational": "理性分析型",
            "intuitive": "直觉感知型",
            "dependent": "参考借鉴型",
            "avoidant": "审慎观望型",
            "spontaneous": "果断行动型",
        }
        parts.append(f"决策风格：{style_map.get(row['decision_style'], row['decision_style'])}")
    if row["maximizer_tendency"]:
        maximizer_map = {
            "maximizer": "追求最优型",
            "satisficer": "务实满意型",
            "mixed": "灵活权衡型",
        }
        parts.append(f"最大化倾向：{maximizer_map.get(row['maximizer_tendency'], row['maximizer_tendency'])}")
    if row["values_ranking"]:
        parts.append(f"价值观排序：{row['values_ranking']}")
    if row["life_stage"]:
        parts.append(f"人生阶段：{row['life_stage']}")
    if row["frequent_dilemma_types"]:
        parts.append(f"常纠结领域：{row['frequent_dilemma_types']}")
    if row["self_intro"]:
        parts.append(f"自我介绍：{row['self_intro']}")

    return "\n".join(parts)


def query_memories(uid: str, memory_type: str, limit: int = 20) -> list[dict]:
    """查询用户的记忆列表，memory_type: episode / core（不支持 semantic）"""
    url = f"{MEMORY_CONFIG['api_url']}/v1/s/memosyne/memoryQuery"
    payload = {
        "appId": MEMORY_CONFIG["app_id"],
        "uid": uid,
        "agentId": MEMORY_CONFIG["agent_id"],
        "repoId": MEMORY_CONFIG["repo_id"],
        "memoryType": memory_type,
        "limit": limit,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            d = data.get("data", {})
            if memory_type == "episode":
                return d.get("episodes", [])
            elif memory_type == "core":
                # cores 返回 map[category][]CoreContent，展平为列表
                cores = d.get("cores", {})
                if isinstance(cores, dict):
                    result = []
                    for category, items in cores.items():
                        if isinstance(items, list):
                            for item in items:
                                item["_category"] = category
                                result.append(item)
                    return result
                return cores if isinstance(cores, list) else []
            return []
        else:
            print(f"[Memory] memoryQuery failed: code={data.get('code')}, msg={data.get('message')}")
            return []
    except Exception as e:
        print(f"[Memory] memoryQuery error: {e}")
        return []


def delete_memories(uid: str, memory_type: str, memory_ids: list[str]) -> bool:
    """删除指定记忆"""
    if not memory_ids:
        return True
    url = f"{MEMORY_CONFIG['api_url']}/v1/s/memosyne/memoryDelete"
    payload = {
        "appId": MEMORY_CONFIG["app_id"],
        "uid": uid,
        "agentId": MEMORY_CONFIG["agent_id"],
        "repoId": MEMORY_CONFIG["repo_id"],
        "memoryType": memory_type,
        "memoryIds": memory_ids,
    }
    try:
        resp = requests.delete(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            return True
        else:
            print(f"[Memory] memoryDelete failed: code={data.get('code')}, msg={data.get('message')}")
            return False
    except Exception as e:
        print(f"[Memory] memoryDelete error: {e}")
        return False


def build_memory_context(uid: str, current_input: str) -> str:
    """
    构建完整的记忆上下文文本，用于拼入 prompt

    包含：
    1. 用户画像（从本地数据库读取）
    2. 相关历史记忆（从 Memosyne API 检索）

    Args:
        uid: 用户ID
        current_input: 用户当前输入

    Returns:
        格式化的记忆上下文文本
    """
    profile = get_user_profile_memory(uid)
    memories = retrieve_memories(uid, current_input, top_n=MEMORY_CONFIG["retrieval_top_n"])

    sections = []
    if profile:
        sections.append(f"## 用户画像\n{profile}")
    if memories:
        memory_lines = "\n".join(f"- {m}" for m in memories)
        sections.append(f"## 你对这个用户的记忆\n{memory_lines}")

    return "\n\n".join(sections)
