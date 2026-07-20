"""
本地记忆系统 — 用 SQLite + LLM 实现简易版记忆提取和检索。

核心思路：
1. 每轮对话后，调 LLM 从对话中提取"记忆事实"（事件、偏好、认知）
2. 存入 memory_facts 表
3. 下次对话前，根据用户输入关键词匹配相关记忆
4. 将匹配到的记忆拼入 prompt
"""
import uuid
import sqlite3
from datetime import datetime
from database import get_db
from clients.llm_client import call_llm


EXTRACT_PROMPT = """你是一个记忆提取器。从以下对话中提取值得长期记住的关键信息。

提取规则：
1. 提取用户透露的事实性信息（事件、状态、偏好、观点、人际关系）
2. 不提取寒暄和无意义内容
3. 每条记忆用一句话概括，主语统一用"用户"
4. 标注类型：event(事件)、preference(偏好)、cognition(认知/观点)、relationship(人际)、status(状态变化)

输出格式（每行一条，用|分隔）：
类型|内容

示例输出：
event|用户最近换了新领导，管理风格很细
preference|用户最在意工作中的成长空间
cognition|用户认为稳定不是钱的问题，是不想重新证明自己
status|用户已经工作3年，想突破但怕风险

如果对话中没有值得提取的信息，输出：无

对话内容：
{conversation}"""


RELEVANCE_PROMPT = """你是一个记忆检索器。根据用户当前的输入，从以下记忆列表中选出最相关的记忆。

用户当前输入：{query}

记忆列表（每行一条，格式为 编号|内容）：
{memories}

请选出最相关的记忆编号（最多5条），用逗号分隔。只输出编号，不要其他内容。
如果没有相关记忆，输出：无"""


def extract_and_store_memories(uid: str, card_id: str, messages: list[dict]):
    """从对话消息中提取记忆事实并存储"""
    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    prompt = EXTRACT_PROMPT.format(conversation=conversation)

    try:
        result = call_llm([{"role": "user", "content": prompt}], model_key="fast")
    except Exception:
        return []

    if "无" in result.strip() and len(result.strip()) < 5:
        return []

    facts = []
    conn = get_db()
    for line in result.strip().split("\n"):
        line = line.strip()
        if "|" not in line:
            continue
        parts = line.split("|", 1)
        if len(parts) != 2:
            continue
        fact_type, content = parts[0].strip(), parts[1].strip()
        if not content or len(content) < 4:
            continue

        fact_id = str(uuid.uuid4())[:8]
        conn.execute(
            "INSERT INTO memory_facts (id, uid, fact_type, content, source_card_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (fact_id, uid, fact_type, content, card_id, datetime.now().isoformat())
        )
        facts.append({"type": fact_type, "content": content})

    conn.commit()
    conn.close()
    return facts


def retrieve_memories(uid: str, query: str, top_n: int = 5) -> list[str]:
    """根据用户输入检索相关记忆"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, fact_type, content FROM memory_facts WHERE uid = ? ORDER BY created_at DESC LIMIT 50",
        (uid,)
    ).fetchall()
    conn.close()

    if not rows:
        return []

    # 如果记忆条数少于等于5，直接全返回
    if len(rows) <= top_n:
        return [row["content"] for row in rows]

    # 用 LLM 做相关性排序
    memories_text = "\n".join(f"{i+1}|{row['content']}" for i, row in enumerate(rows))
    prompt = RELEVANCE_PROMPT.format(query=query, memories=memories_text)

    try:
        result = call_llm([{"role": "user", "content": prompt}], model_key="fast")
    except Exception:
        # LLM 失败时返回最近的几条
        return [row["content"] for row in rows[:top_n]]

    if "无" in result.strip() and len(result.strip()) < 5:
        return []

    # 解析编号
    selected = []
    for part in result.strip().replace(" ", "").split(","):
        try:
            idx = int(part) - 1
            if 0 <= idx < len(rows):
                selected.append(rows[idx]["content"])
        except ValueError:
            continue

    return selected[:top_n] if selected else [row["content"] for row in rows[:top_n]]


def get_user_profile_memory(uid: str) -> str:
    """获取用户画像的文本描述（从 users 表）"""
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
    conn.close()

    if not row:
        return ""

    parts = []
    if row["mbti"]:
        parts.append(f"MBTI类型：{row['mbti']}")
    if row["decision_style"]:
        style_map = {"avoidant": "回避型", "impulsive": "冲动型", "rational": "理性型", "dependent": "依赖型"}
        parts.append(f"决策风格：{style_map.get(row['decision_style'], row['decision_style'])}")
    if row["values_ranking"]:
        parts.append(f"价值观排序：{row['values_ranking']}")
    if row["life_stage"]:
        parts.append(f"人生阶段：{row['life_stage']}")
    if row["frequent_dilemma_types"]:
        parts.append(f"常纠结领域：{row['frequent_dilemma_types']}")

    return "\n".join(parts)


def build_memory_context(uid: str, current_input: str) -> str:
    """构建完整的记忆上下文文本，用于拼入 prompt"""
    profile = get_user_profile_memory(uid)
    memories = retrieve_memories(uid, current_input)

    sections = []
    if profile:
        sections.append(f"## 用户画像\n{profile}")
    if memories:
        memory_lines = "\n".join(f"- {m}" for m in memories)
        sections.append(f"## 你对这个用户的记忆\n{memory_lines}")

    return "\n\n".join(sections)
