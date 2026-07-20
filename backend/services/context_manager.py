"""
智能对话上下文管理 - 针对"不纠结"场景优化

策略：滑动窗口 + 初始摘要
- 对话 ≤ 20 轮：全部原文
- 对话 > 20 轮：前期摘要 + 最近 10 轮原文
"""

# 配置参数
CONTEXT_CONFIG = {
    "max_recent_turns": 10,      # 保留最近 N 轮原文
    "summary_threshold": 20,      # 超过 N 轮才做摘要
    "max_context_tokens": 6000,   # 上下文最大 token 数（预留给回复）
}


def get_card_context_messages(card_id: str) -> list[dict]:
    """
    获取卡片的对话上下文（智能截断）

    策略：
    - 对话 ≤ 20 轮：返回全部原文
    - 对话 > 20 轮：返回【前期摘要 + 最近 10 轮原文】

    Returns:
        消息列表，格式：[{"role": "...", "content": "..."}, ...]
    """
    from database import get_db

    conn = get_db()
    all_msgs = conn.execute(
        "SELECT role, content FROM messages WHERE card_id = ? ORDER BY created_at ASC",
        (card_id,)
    ).fetchall()
    conn.close()

    all_messages = [{"role": m["role"], "content": m["content"]} for m in all_msgs]

    # 计算用户轮次
    user_turns = sum(1 for m in all_messages if m["role"] == "user")

    # 策略 1：对话不长，全部返回
    if user_turns <= CONTEXT_CONFIG["summary_threshold"]:
        return all_messages

    # 策略 2：长对话，分段处理
    # 最近 N 轮 = 最后 2N 条消息（user + assistant）
    recent_count = CONTEXT_CONFIG["max_recent_turns"] * 2
    recent_messages = all_messages[-recent_count:]
    old_messages = all_messages[:-recent_count]

    # 获取或生成旧消息的摘要
    summary_text = _get_or_create_context_summary(card_id, old_messages)

    # 构建最终上下文：摘要 + 最近原文
    context_messages = [
        {"role": "system", "content": f"【前期对话摘要】\n{summary_text}"}
    ]
    context_messages.extend(recent_messages)

    return context_messages


def _get_or_create_context_summary(card_id: str, old_messages: list[dict]) -> str:
    """
    获取或创建对话摘要（带缓存）

    缓存策略：
    - 摘要存在 cards 表的 context_summary 字段
    - 只有当 old_messages 长度变化时才重新生成
    """
    from database import get_db
    from clients.llm_client import call_llm

    conn = get_db()
    card = conn.execute(
        "SELECT context_summary, context_summary_length FROM cards WHERE id = ?",
        (card_id,)
    ).fetchone()
    conn.close()

    current_length = len(old_messages)

    # 如果有缓存且长度匹配，直接返回
    if card and card["context_summary"] and card["context_summary_length"] == current_length:
        return card["context_summary"]

    # 否则，生成新摘要
    summary = _summarize_context(old_messages)

    # 更新缓存
    conn = get_db()
    conn.execute(
        "UPDATE cards SET context_summary = ?, context_summary_length = ? WHERE id = ?",
        (summary, current_length, card_id)
    )
    conn.commit()
    conn.close()

    return summary


def _summarize_context(messages: list[dict]) -> str:
    """用 LLM 生成对话摘要"""
    from clients.llm_client import call_llm

    if not messages:
        return ""

    # 构建对话文本
    conversation = "\n".join(
        f"{m['role']}: {m['content']}" for m in messages
    )

    prompt = f"""请用 200-300 字总结以下对话的核心内容，保留关键信息：

对话内容：
{conversation}

总结要求：
1. 保留用户的核心纠结点
2. 保留已经讨论过的重要因素
3. 保留用户表达的倾向
4. 用第三人称描述
5. 简洁但完整

摘要："""

    try:
        summary = call_llm([{"role": "user", "content": prompt}])
        return summary.strip()
    except Exception as e:
        print(f"[Context] Summary generation failed: {e}")
        # 降级方案：简单拼接前几轮
        fallback = " / ".join(
            m["content"][:50] for m in messages[:5] if m["role"] == "user"
        )
        return f"早期对话涉及：{fallback}..."


# 使用示例
def handle_chat_with_smart_context(uid: str, card_id: str, user_message: str):
    """
    处理对话（使用智能上下文）
    """
    # 1. 获取智能截断的上下文
    context_messages = get_card_context_messages(card_id)

    # 2. 构建 prompt
    from services.chat_service import build_system_prompt

    system_prompt = build_system_prompt(uid, user_message, stage="exploring")

    # 3. 拼接完整消息
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    messages.extend(context_messages)
    messages.append({"role": "user", "content": user_message})

    # 4. 调用 LLM
    from clients.llm_client import call_llm
    response = call_llm(messages)

    return response


# 数据库迁移
"""
需要给 cards 表增加两个字段：

ALTER TABLE cards ADD COLUMN context_summary TEXT;
ALTER TABLE cards ADD COLUMN context_summary_length INTEGER DEFAULT 0;
"""
