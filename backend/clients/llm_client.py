import requests
from config import LLM_CONFIG


def call_llm(messages: list[dict], model_key: str = "main", temperature: float = None, max_tokens: int = None) -> str:
    model_info = LLM_CONFIG["models"][model_key]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model_info['key']}"
    }
    payload = {
        "model": model_info["id"],
        "messages": messages,
        "temperature": temperature or LLM_CONFIG["temperature"],
        "max_tokens": max_tokens or LLM_CONFIG["max_tokens"],
    }
    resp = requests.post(LLM_CONFIG["api_url"], json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_llm_json(messages: list[dict], model_key: str = "main") -> str:
    """
    Call LLM expecting structured JSON output.
    Uses JSON mode if supported, otherwise relies on prompt instructions.
    Retries once if first attempt returns invalid JSON.
    """
    model_info = LLM_CONFIG["models"][model_key]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {model_info['key']}"
    }

    payload = {
        "model": model_info["id"],
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": LLM_CONFIG["max_tokens"],
    }

    # 尝试最多2次
    for attempt in range(2):
        try:
            # 第一次尝试使用 JSON mode
            if attempt == 0:
                payload_with_json_mode = payload.copy()
                payload_with_json_mode["response_format"] = {"type": "json_object"}
                resp = requests.post(LLM_CONFIG["api_url"], json=payload_with_json_mode, headers=headers, timeout=30)
            else:
                # 第二次尝试普通调用 + 增强 prompt
                retry_messages = messages.copy()
                retry_messages.append({
                    "role": "user",
                    "content": "请严格按照 JSON 格式返回，不要有任何格式错误。"
                })
                payload["messages"] = retry_messages
                resp = requests.post(LLM_CONFIG["api_url"], json=payload, headers=headers, timeout=30)

            resp.raise_for_status()
            result = resp.json()

            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]

                # 验证是否是有效 JSON（宽松验证）
                import json
                try:
                    json.loads(content)
                    return content  # 有效 JSON，直接返回
                except json.JSONDecodeError as e:
                    if attempt == 0:
                        print(f"[LLM] Attempt {attempt + 1} returned invalid JSON: {e}, retrying...")
                        continue  # 重试
                    else:
                        print(f"[LLM] Attempt {attempt + 1} also failed, returning as-is")
                        return content  # 第二次也失败，返回原始内容让解析器处理

        except Exception as e:
            print(f"[LLM] Attempt {attempt + 1} failed with exception: {e}")
            if attempt == 1:
                break  # 第二次也失败，停止重试

    # 所有尝试都失败，返回空 JSON
    return "{}"
