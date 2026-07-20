"""
核心对话编排服务 — 处理每轮对话的完整流程。
"""
import json
import uuid
from datetime import datetime
from database import get_db
from clients.llm_client import call_llm, call_llm_json
from clients.memory_client import build_memory_context, extract_and_store_memories
from prompts.templates import (
    BASE_ROLE, STAGE_CLARIFYING, STAGE_EXPLORING,
    STAGE_ADVISING, STAGE_CLOSING, CARD_EXTRACT, MEMORY_SUMMARY,
    CHECK_READY_FOR_ADVICE, INSIGHT_EXTRACT, VALUE_CONFLICT_CHECK
)


def _parse_structured_response(raw_response: str) -> dict:
    """
    宽松解析 LLM 返回，支持多种格式。
    返回: {"message": str, "progress_hint": dict | None}
    """
    try:
        # 1. 清理 markdown 代码块
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # 移除第一行的 ```json 或 ```
            cleaned = "\n".join(lines[1:])
            # 移除最后的 ```
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0].strip()

        # 2. 修复常见的 JSON 错误（字段重复问题）
        # 例如 "label": "label": "xxx" -> "label": "xxx"
        import re
        cleaned = re.sub(r'"(\w+)":\s*"\1":\s*', r'"\1": ', cleaned)
        # 移除多余的逗号 ","," -> ","
        cleaned = re.sub(r',\s*,+', ',', cleaned)
        # 移除尾随逗号（对象末尾的 ,}）
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)

        # 3. 尝试解析 JSON
        data = json.loads(cleaned)

        # 4. 校验必需字段
        if "message" not in data:
            raise ValueError("Missing 'message' field")

        # 5. 校验 progress_hint 格式（可选字段）
        hint = data.get("progress_hint")
        if hint:
            if not isinstance(hint, dict) or "label" not in hint:
                hint = None  # 格式不对就丢弃
            else:
                # 确保 tendency 格式正确（如果存在）
                if "tendency" in hint and hint["tendency"] is not None:
                    tendency = hint["tendency"]
                    if not isinstance(tendency, dict) or \
                       "option_a" not in tendency or "option_b" not in tendency:
                        hint["tendency"] = None  # 格式不对就清空

        return {
            "message": data["message"],
            "progress_hint": hint
        }

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # JSON 解析失败，尝试模糊提取
        print(f"[Chat] JSON parsing failed: {e}, trying fuzzy extraction")

        # 模糊提取：尝试从文本中提取 message 和基本字段
        try:
            # 尝试找到 "message": "..." 部分（支持含转义引号的内容）
            message_match = re.search(r'"message"\s*:\s*"((?:[^"\\]|\\.)*)"', raw_response)
            label_match = re.search(r'"label"\s*:\s*"((?:[^"\\]|\\.)*)"', raw_response)

            if message_match:
                message = message_match.group(1)
                # 只处理 JSON 转义（\n, \"等），不做 unicode_escape 以保留中文
                message = message.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')

                hint = None
                if label_match:
                    label = label_match.group(1)
                    label = label.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                    hint = {"label": label, "tendency": None, "next_question": ""}

                    # 尝试提取 next_question
                    nq_match = re.search(r'"next_question"\s*:\s*"((?:[^"\\]|\\.)*)"', raw_response)
                    if nq_match:
                        nq = nq_match.group(1).replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                        hint["next_question"] = nq

                    # 尝试提取 tendency
                    ta_match = re.search(r'"option_a"\s*:\s*(\d+)', raw_response)
                    tb_match = re.search(r'"option_b"\s*:\s*(\d+)', raw_response)
                    if ta_match and tb_match:
                        hint["tendency"] = {
                            "option_a": int(ta_match.group(1)),
                            "option_b": int(tb_match.group(1))
                        }

                return {
                    "message": message,
                    "progress_hint": hint
                }
        except Exception as e2:
            print(f"[Chat] Fuzzy extraction also failed: {e2}")

        # 完全失败，整段当作 message
        return {
            "message": raw_response,
            "progress_hint": None
        }


def _infer_options(card: dict, history: list[dict], tendency: dict = None) -> list[str]:
    """
    从卡片信息和对话推断 A/B 选项名称。
    优先使用大模型返回的 option_a_label/option_b_label，
    其次用规则匹配，最后用类型默认值。
    """
    # 优先使用大模型返回的选项名（如果有）
    if tendency:
        option_a_label = tendency.get("option_a_label")
        option_b_label = tendency.get("option_b_label")
        if option_a_label and option_b_label:
            return [option_a_label, option_b_label]

    # 回退到规则匹配
    # 先尝试从对话内容中提取具体选项
    trigger = card.get("trigger_event", "") or card.get("initial_input", "") or ""
    core_conflict = card.get("core_conflict", "") or ""
    search_text = trigger + " " + core_conflict

    # 从前几轮对话中收集文本
    for msg in history[:6]:
        search_text += " " + msg.get("content", "")

    # 根据关键词匹配更精确的选项名
    # 创业 vs 留下
    if "创业" in search_text:
        return ["创业", "留下"]
    # 跳槽/新offer vs 留下
    if "offer" in search_text.lower() or "跳槽" in search_text or "新公司" in search_text:
        return ["跳槽", "留下"]
    # 考研 vs 工作
    if "考研" in search_text or "读研" in search_text:
        return ["考研", "工作"]
    # 出国 vs 留在国内
    if "出国" in search_text or "留学" in search_text:
        return ["出国", "留下"]
    # 分手 vs 继续
    if "分手" in search_text:
        return ["分手", "继续"]
    # 表白 vs 不说
    if "表白" in search_text or "暧昧" in search_text:
        return ["表白", "不说"]
    # 买 vs 不买
    if "买" in search_text and ("不买" in search_text or "值不值" in search_text):
        return ["买", "不买"]

    # 尝试从对话中找"还是"关键词
    for msg in history[:6]:
        content = msg.get("content", "")
        if "还是" in content:
            parts = content.split("还是", 1)
            if len(parts) == 2:
                option_a = parts[0].strip()[-10:].strip()
                option_b = parts[1].strip()[:10].strip()
                if option_a and option_b:
                    return [option_a, option_b]

    # 类型默认值兜底
    dilemma_type = card.get("dilemma_type", "")
    type_defaults = {
        "career": ["改变", "留下"],
        "finance": ["买", "不买"],
        "education": ["选A", "选B"],
        "lifestyle": ["改变", "维持"],
        "growth": ["坚持", "放弃"],
        "relationship": ["行动", "观望"],
    }

    return type_defaults.get(dilemma_type, ["选项A", "选项B"])


def _should_extract_memory(card_id: str) -> bool:
    """判断是否应该触发记忆提取（每 10 轮对话提取一次）"""
    conn = get_db()
    user_msg_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE card_id = ? AND role = 'user'",
        (card_id,)
    ).fetchone()['cnt']
    conn.close()
    # 每 10 轮用户消息提取一次（第 10、20、30... 轮）
    return user_msg_count > 0 and user_msg_count % 10 == 0


def _summarize_old_messages(messages: list[dict]) -> str:
    """用 LLM 总结历史消息，返回摘要文本"""
    if not messages:
        return ""

    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    prompt = MEMORY_SUMMARY.format(conversation=conversation)

    try:
        summary = call_llm([{"role": "user", "content": prompt}])
        return summary.strip()
    except Exception as e:
        print(f"[Memory] Failed to summarize old messages: {e}")
        # 如果总结失败，返回简单拼接
        return f"前期对话摘要：用户与助手进行了 {len(messages)//2} 轮对话。"


def _build_context_with_fallback(history: list[dict]) -> list[dict]:
    """
    智能构建对话上下文，带兜底压缩机制

    策略：
    - 对话 ≤ 50 轮（100 条消息）：全部保留
    - 对话 > 50 轮：前期压缩 + 保留最近 30 轮原文

    Args:
        history: 完整对话历史

    Returns:
        处理后的上下文消息列表
    """
    # 配置参数
    FALLBACK_THRESHOLD = 100  # 兜底阈值：100 条消息（50 轮）
    RECENT_KEEP_COUNT = 60    # 保留最近 60 条消息（30 轮）

    # 策略 1：对话不长，全部保留
    if len(history) <= FALLBACK_THRESHOLD:
        return history

    # 策略 2：对话很长，触发兜底压缩
    print(f"[Context] 对话过长（{len(history)} 条消息），触发兜底压缩")

    # 分段：旧消息 + 最近消息
    recent_messages = history[-RECENT_KEEP_COUNT:]
    old_messages = history[:-RECENT_KEEP_COUNT]

    # 压缩旧消息
    try:
        summary = _summarize_old_messages(old_messages)

        # 构建压缩后的上下文
        compressed_context = [
            {"role": "system", "content": f"【前期对话压缩摘要】\n{summary}"}
        ]
        compressed_context.extend(recent_messages)

        print(f"[Context] 压缩完成：{len(old_messages)} 条 → 摘要，保留最近 {len(recent_messages)} 条")
        return compressed_context

    except Exception as e:
        print(f"[Context] 压缩失败，降级为截断: {e}")
        # 压缩失败，降级为简单截断
        return history[-FALLBACK_THRESHOLD:]


def _build_messages_for_extraction(card_id: str) -> list[dict]:
    """构建用于记忆提取的消息列表：历史摘要 + 最近 10 轮原文"""
    full_history = get_card_messages(card_id)

    # 如果总对话不超过 20 条消息（10 轮），直接返回全部
    if len(full_history) <= 20:
        return full_history

    # 否则：旧对话做摘要 + 最近 10 轮原文
    # 最近 10 轮 = 最后 20 条消息
    recent_messages = full_history[-20:]
    old_messages = full_history[:-20]

    # 总结旧对话
    summary = _summarize_old_messages(old_messages)

    # 构建消息列表：summary 作为 system 角色插入开头
    messages_with_context = [
        {"role": "system", "content": f"【前期对话摘要】{summary}"}
    ]
    messages_with_context.extend(recent_messages)

    return messages_with_context


def _extract_memories_task(uid: str, card_id: str, messages: list[dict]):
    """后台任务：提取并存储记忆"""
    try:
        extract_and_store_memories(uid, card_id, messages)
    except Exception as e:
        print(f"[Memory] Background extraction failed for card {card_id}: {e}")


def _check_ready_for_advice(uid: str, messages: list[dict]) -> bool:
    """用 LLM 判断是否有足够信息给出建议"""
    from clients.memory_client import get_user_profile_memory

    # 构建对话历史
    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in messages)

    # 获取用户档案
    profile_text = get_user_profile_memory(uid)

    # 调用 LLM 判断
    prompt = CHECK_READY_FOR_ADVICE.replace("{conversation}", conversation).replace("{profile}", profile_text)
    try:
        result = call_llm_json([{"role": "user", "content": prompt}])
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(result)
        return data.get("ready", False)
    except Exception as e:
        print(f"[Stage] Failed to check readiness: {e}")
        return False



def _split_values_ranking(raw: str) -> list[str]:
    """兼容 values_ranking 的历史分隔符：>, 顿号和中英文逗号。"""
    import re

    return [v.strip() for v in re.split(r"[>、,，]+", raw or "") if v.strip()]

def _check_value_conflict(uid: str, card_id: str, messages: list[dict]) -> dict | None:
    """
    检查用户实际关注点是否与声称价值观冲突（MVP 方案）

    每 5 轮检查一次，如果实际关注点与声称的前 3 个价值观不一致，返回提示

    Args:
        uid: 用户ID
        card_id: 卡片ID（预留，暂未使用）
        messages: 对话历史

    Returns:
        {"conflict": true, "declared_top": "...", "actual_focus": "...", "suggestion": "..."}
        或 None（如果一致或检查失败）
    """
    conn = get_db()
    user = conn.execute("SELECT values_ranking FROM users WHERE uid = ?", (uid,)).fetchone()
    conn.close()

    if not user or not user["values_ranking"]:
        return None

    top_values = _split_values_ranking(user["values_ranking"])[:3]
    if not top_values:
        return None

    # 只检查最近 10 轮对话
    recent = messages[-20:] if len(messages) > 20 else messages
    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in recent)

    prompt = (
        VALUE_CONFLICT_CHECK
        .replace("{top_values}", ", ".join(top_values))
        .replace("{conversation}", conversation)
        .replace("{declared_top}", top_values[0])
    )

    try:
        result = call_llm_json([{"role": "user", "content": prompt}])
        # 清理 markdown 包裹
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]

        data = json.loads(result)
        return data if data.get("conflict") else None
    except Exception as e:
        print(f"[ValueConflict] Check failed: {e}")
        return None


def determine_stage(card: dict, messages: list[dict], uid: str) -> str:
    """根据对话轮次和内容判断当前阶段"""
    user_turns = [m for m in messages if m["role"] == "user"]
    turn_count = len(user_turns)

    # 卡片已关闭
    if card["status"] in ("decided", "shelved"):
        return "closing"

    # 前3轮且卡片还没有结构化信息 → 追问阶段
    if turn_count <= 3 and not card["core_conflict"]:
        return "clarifying"

    # 检查用户是否表达了决定
    if user_turns:
        last_msg = user_turns[-1]["content"]

        # 明确的决定（精确关键词）
        strong_decision_keywords = ["我决定", "我想好了", "就这么办", "我要这样做", "我确定了"]
        if any(kw in last_msg for kw in strong_decision_keywords):
            return "closing"

        # 用户明确要建议 → 立即进入 advising（不管轮次）
        ask_advice_keywords = ["你觉得", "你认为", "你建议", "给个建议", "怎么看", "你的意见", "你推荐", "应该怎么"]
        if any(kw in last_msg for kw in ask_advice_keywords):
            return "advising"

    # 第15轮后：每轮都判断是否该给建议（用户可能不满意上次建议，或还想继续聊）
    if turn_count >= 15:
        # 即使之前给过建议，如果用户继续对话，说明还有疑问，持续判断
        if _check_ready_for_advice(uid, messages):
            return "advising"
        else:
            # 如果判断不够，继续探索
            return "exploring"

    # 从第5轮开始，用 LLM 判断信息是否足够给建议
    if turn_count >= 5:
        if _check_ready_for_advice(uid, messages):
            return "advising"

    return "exploring"


def get_stage_prompt(stage: str) -> str:
    """获取对应阶段的指令"""
    stage_map = {
        "clarifying": STAGE_CLARIFYING,
        "exploring": STAGE_EXPLORING,
        "advising": STAGE_ADVISING,
        "closing": STAGE_CLOSING,
    }
    return stage_map.get(stage, STAGE_EXPLORING)


def build_system_prompt(uid: str, current_input: str, stage: str, card: dict = None) -> str:
    """组装完整的 system prompt（包含个性化策略）"""
    from prompts.personality_prompts import GDMS_PROMPTS, MAXIMIZER_PROMPTS, VALUE_PROMPTS, MBTI_PROMPTS

    # 读取用户画像
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
    conn.close()

    # 构建记忆上下文和阶段指令（保留原有逻辑）
    memory_context = build_memory_context(uid, current_input)
    stage_prompt = get_stage_prompt(stage)

    parts = [BASE_ROLE]

    # 1. 基础用户画像（简化版）
    if user:
        profile_parts = []
        if user["decision_style"]:
            style_map = {
                "rational": "理性分析型",
                "intuitive": "直觉感知型",
                "dependent": "参考借鉴型",
                "avoidant": "审慎观望型",
                "spontaneous": "果断行动型",
            }
            style_key = user["decision_style"]
            if "_" in style_key:  # 组合型
                parts_list = style_key.split("_")
                if len(parts_list) == 2 and parts_list[0] in style_map and parts_list[1] in style_map:
                    profile_parts.append(f"决策风格：{style_map[parts_list[0]]} + {style_map[parts_list[1]]}")
                else:
                    profile_parts.append(f"决策风格：{style_map.get(style_key, style_key)}")
            else:
                profile_parts.append(f"决策风格：{style_map.get(style_key, style_key)}")

        if user["maximizer_tendency"]:
            max_map = {"maximizer": "追求最优型", "satisficer": "务实满意型", "mixed": "灵活权衡型"}
            profile_parts.append(f"倾向：{max_map.get(user['maximizer_tendency'], user['maximizer_tendency'])}")

        if user["mbti"] and user["mbti"] != "unknown":
            profile_parts.append(f"MBTI：{user['mbti']}")

        if user["values_ranking"]:
            values = _split_values_ranking(user["values_ranking"])[:3]
            profile_parts.append(f"核心价值观：{', '.join(values)}")

        if profile_parts:
            parts.append(f"【用户画像】\n" + "\n".join(profile_parts))

    # 2. 历史记忆（保留原有逻辑）
    if memory_context:
        parts.append(memory_context)

    # 3. 注入 GDMS 风格策略
    if user and user["decision_style"]:
        style_key = user["decision_style"]

        # 处理组合型：拆分并拼接两个单一风格的 Prompt
        if "_" in style_key:
            styles = style_key.split("_")
            if len(styles) == 2:
                primary_style = styles[0]    # 主风格（得分更高或排序靠前）
                secondary_style = styles[1]  # 次风格

                primary_prompt = GDMS_PROMPTS.get(primary_style)
                secondary_prompt = GDMS_PROMPTS.get(secondary_style)

                if primary_prompt and secondary_prompt:
                    # 添加组合说明
                    combo_intro = f"""【决策风格：组合型】
用户同时具备两种决策风格，需要综合考虑：
• 主要风格（{primary_style}）：在大多数情况下，用户倾向于这种方式
• 次要风格（{secondary_style}）：在特定场景下，用户也会表现出这种特点

策略：优先满足主要风格的需求，同时兼顾次要风格的特点。"""

                    parts.append(combo_intro)
                    parts.append(f"【主要风格策略】\n{primary_prompt}")
                    parts.append(f"【次要风格策略】\n{secondary_prompt}")
                else:
                    # 如果找不到对应 Prompt，降级处理
                    if primary_prompt:
                        parts.append(f"【决策风格策略】\n{primary_prompt}")
            else:
                # 无法拆分的情况，尝试直接查找
                style_prompt = GDMS_PROMPTS.get(style_key)
                if style_prompt:
                    parts.append(f"【决策风格策略】\n{style_prompt}")

        # 处理单一风格
        else:
            style_prompt = GDMS_PROMPTS.get(style_key)
            if style_prompt:
                parts.append(f"【决策风格策略】\n{style_prompt}")

    # 4. 注入最大化倾向策略
    if user and user["maximizer_tendency"]:
        max_prompt = MAXIMIZER_PROMPTS.get(user["maximizer_tendency"])
        if max_prompt:
            parts.append(f"【倾向策略】\n{max_prompt}")

    # 5. 注入价值观策略（前 3 个）
    if user and user["values_ranking"]:
        values = _split_values_ranking(user["values_ranking"])[:3]
        for val in values:
            val_prompt = VALUE_PROMPTS.get(val)
            if val_prompt:
                parts.append(val_prompt)  # 已包含标题，不需要额外添加

    # 6. 注入 MBTI 策略（可选）
    if user and user["mbti"] and user["mbti"] != "unknown":
        mbti_prompt = MBTI_PROMPTS.get(user["mbti"])
        if mbti_prompt:
            parts.append(f"【MBTI：{user['mbti']}】{mbti_prompt}")

    # 7. 注入历史倾向（保留原有逻辑）
    if card and card.get("current_tendency"):
        try:
            tendency = json.loads(card["current_tendency"])
            if tendency.get("options") and tendency.get("option_a") is not None:
                parts.append(
                    f"【当前倾向】用户在上一轮表达的倾向分布：{tendency['options'][0]} {tendency['option_a']}% "
                    f"vs {tendency['options'][1]} {tendency['option_b']}%。本轮评估时参考此基线。"
                )
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # 8. 注入阶段指令
    parts.append(stage_prompt)

    return "\n\n".join(parts)


def get_card_messages(card_id: str) -> list[dict]:
    """获取卡片内所有对话消息"""
    conn = get_db()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE card_id = ? ORDER BY created_at ASC",
        (card_id,)
    ).fetchall()
    conn.close()
    return [{"role": row["role"], "content": row["content"]} for row in rows]


def save_message(card_id: str, role: str, content: str):
    """保存一条消息"""
    conn = get_db()
    msg_id = str(uuid.uuid4())[:8]
    conn.execute(
        "INSERT INTO messages (id, card_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (msg_id, card_id, role, content, datetime.now().isoformat())
    )
    conn.execute(
        "UPDATE cards SET updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), card_id)
    )
    conn.commit()
    conn.close()


def extract_card_info(card_id: str):
    """追问阶段结束后，从对话中提取卡片结构化信息"""
    messages = get_card_messages(card_id)
    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    prompt = CARD_EXTRACT.format(conversation=conversation)

    try:
        result = call_llm_json([{"role": "user", "content": prompt}])
        # 清理可能的 markdown 包裹
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            result = result.rsplit("```", 1)[0]
        card_info = json.loads(result)
    except (json.JSONDecodeError, Exception):
        return None

    conn = get_db()
    conn.execute(
        """UPDATE cards SET title = ?, core_conflict = ?, trigger_event = ?, main_concern = ?, updated_at = ?
           WHERE id = ?""",
        (card_info.get("title", ""), card_info.get("core_conflict", ""),
         card_info.get("trigger_event", ""), card_info.get("main_concern", ""),
         datetime.now().isoformat(), card_id)
    )
    conn.commit()
    conn.close()
    return card_info


def _auto_close_card_if_decided(card_id: str, user_message: str, assistant_message: str, background_tasks=None) -> bool:
    """检查用户是否做出最终决定，如果是则自动关闭卡片"""
    import re

    # 明确的决定关键词（精确匹配，必须是真正的决定）
    decision_indicators = [
        "我决定了",
        "我想好了",
        "就这么办",
        "我要这样做",
        "我确定了",
        "就这样了",
        "我选择了",
    ]

    # 宽松模式匹配（"我决定" + 具体行动）
    decision_patterns = [
        r"我决定.{1,10}了[，。！\s]*$",   # "我决定接offer了"（句尾）
        r"^我决定.{1,15}$",                # "我决定跳槽"（整句）
        r"决定了[，。！]\s*谢谢",          # "决定了，谢谢你"
        r"想清楚了[，。！]",                # "我想清楚了"
    ]

    # 检查用户消息
    user_decided = any(kw in user_message for kw in decision_indicators)
    if not user_decided:
        user_decided = any(re.search(p, user_message) for p in decision_patterns)

    # **删除了对 AI 回复的检查** - AI 说"我在这儿"不代表用户做了决定
    # 只有用户明确表达决定，才关闭卡片

    if user_decided:
        from services.card_service import close_card
        close_card(card_id, "decided", decision_result="用户已做出决定", decision_reason="对话自然结束")

        # 自动关闭后也要生成 Insight
        if background_tasks:
            background_tasks.add_task(generate_insight, card_id)

        return True

    return False


def chat(uid: str, card_id: str, user_message: str, background_tasks=None) -> dict:
    """
    核心对话方法。

    Args:
        background_tasks: FastAPI BackgroundTasks 实例，用于异步提取记忆

    返回:
        {
            "assistant_message": str,
            "progress_hint": dict | None,
            "stage": str,
            "card_updated": bool,
            "card_info": dict | None,
            "card_closed": bool
        }
    """
    # 1. 保存用户消息
    save_message(card_id, "user", user_message)

    # 2. 获取卡片信息
    conn = get_db()
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    conn.close()
    if not card:
        return {
            "assistant_message": "找不到这张卡片",
            "progress_hint": None,
            "stage": "error",
            "card_updated": False,
            "card_info": None,
            "card_closed": False
        }
    card = dict(card)

    # 3. 获取对话历史
    history = get_card_messages(card_id)

    # 4. 判断阶段
    stage = determine_stage(card, history, uid)

    # 5. 组装 system prompt（注入历史倾向）
    system_prompt = build_system_prompt(uid, user_message, stage, card)

    # 6. 构建 LLM messages
    llm_messages = [{"role": "system", "content": system_prompt}]

    # 智能上下文管理：正常情况全部拼接，极端情况压缩旧对话
    context_messages = _build_context_with_fallback(history)
    llm_messages.extend(context_messages)

    # 7. 调用 LLM（使用结构化 JSON 返回，带 fallback）
    assistant_message = ""
    progress_hint = None
    try:
        raw_reply = call_llm_json(llm_messages)
        parsed = _parse_structured_response(raw_reply)
        assistant_message = parsed["message"]
        progress_hint = parsed["progress_hint"]
    except Exception as e:
        print(f"[Chat] call_llm_json failed, fallback to call_llm: {e}")
        try:
            assistant_message = call_llm(llm_messages)
            progress_hint = None
        except Exception as e2:
            print(f"[Chat] call_llm also failed: {e2}")
            assistant_message = "抱歉，我暂时无法回应，请稍后再试。"
            progress_hint = None

    # 8. 保存助手回复
    save_message(card_id, "assistant", assistant_message)

    # 9. 更新倾向数据（如果 progress_hint 包含 tendency）
    if progress_hint and progress_hint.get("tendency"):
        tendency = progress_hint["tendency"]
        # 只有当 tendency 不为 null 且格式正确时才存储
        if tendency.get("option_a") is not None and tendency.get("option_b") is not None:
            # 优先使用大模型返回的选项名，否则用规则匹配
            options = _infer_options(card, history, tendency)
            tendency_data = {
                "option_a": int(tendency["option_a"]),
                "option_b": int(tendency["option_b"]),
                "options": options
            }

            conn = get_db()
            conn.execute(
                "UPDATE cards SET current_tendency = ?, updated_at = ? WHERE id = ?",
                (json.dumps(tendency_data, ensure_ascii=False), datetime.now().isoformat(), card_id)
            )
            conn.commit()
            conn.close()

    # 10. 条件触发记忆提取（每 10 轮提取一次，带历史摘要）
    if background_tasks and _should_extract_memory(card_id):
        messages_to_extract = _build_messages_for_extraction(card_id)
        background_tasks.add_task(_extract_memories_task, uid, card_id, messages_to_extract)

    # 11. 如果追问阶段结束（第3轮用户回复后），提取卡片信息
    card_info = None
    card_updated = False
    user_turns = [m for m in history if m["role"] == "user"]
    if len(user_turns) >= 2 and not card["core_conflict"]:
        card_info = extract_card_info(card_id)
        if card_info:
            card_updated = True

    # 12. 检查是否应该自动关闭卡片
    card_closed = _auto_close_card_if_decided(card_id, user_message, assistant_message, background_tasks)

    # 13. 价值观冲突识别（每 5 轮检查一次）
    value_conflict_hint = None
    user_turns = [m for m in history if m["role"] == "user"]
    if len(user_turns) % 5 == 0 and len(user_turns) >= 5:
        value_conflict_hint = _check_value_conflict(uid, card_id, history)

    # 14. 进入建议阶段时，附带一条相似社区案例（前端负责"每会话只展示一次"）
    related_case = None
    if stage == "advising":
        try:
            from services.case_service import find_related_case
            related_case = find_related_case(card, exclude_card_id=card_id)
        except Exception as e:
            print(f"[Case] find_related_case failed: {e}")

    # 15. 在 progress_hint 的 tendency 中注入选项名，方便前端展示
    if progress_hint and progress_hint.get("tendency"):
        # 优先使用大模型返回的选项名，否则用规则匹配
        options = _infer_options(card, history, progress_hint["tendency"])
        progress_hint["tendency"]["options"] = options

    return {
        "assistant_message": assistant_message,
        "progress_hint": progress_hint,
        "stage": stage,
        "card_updated": card_updated,
        "card_info": card_info,
        "card_closed": card_closed,
        "value_conflict_hint": value_conflict_hint,
        "related_case": related_case,  # 新增：相似社区案例
    }


def generate_insight(card_id: str):
    """
    关闭卡片时生成 Insight。
    从对话中提取核心矛盾、价值观信号、担忧类型、行动建议。
    """
    messages = get_card_messages(card_id)
    if not messages:
        return

    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    prompt = INSIGHT_EXTRACT.format(conversation=conversation)

    try:
        result = call_llm_json([{"role": "user", "content": prompt}])
        # 清理可能的 markdown 包裹
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]

        insight_data = json.loads(result)

        # 存入 cards 表
        conn = get_db()
        conn.execute(
            "UPDATE cards SET insight = ?, updated_at = ? WHERE id = ?",
            (json.dumps(insight_data, ensure_ascii=False), datetime.now().isoformat(), card_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Insight] Failed to generate insight for card {card_id}: {e}")




