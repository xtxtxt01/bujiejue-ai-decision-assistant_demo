import os

# LLM API 配置（讯飞星火 MaaS 平台）
LLM_CONFIG = {
    "api_url": os.getenv("LLM_API_URL", "https://maas-api.cn-huabei-1.xf-yun.com/v2/chat/completions"),
    "models": {
        "main": {
            "id": os.getenv("LLM_MAIN_MODEL_ID", "xopdeepseekv4flash"),
            "key": os.getenv("LLM_MAIN_API_KEY", "")
        },
        "fast": {
            "id": os.getenv("LLM_FAST_MODEL_ID", "xop3qwen4b"),
            "key": os.getenv("LLM_FAST_API_KEY", "")
        },
    },
    "temperature": 0.7,
    "max_tokens": 2048,
}

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")

# Memosyne 记忆系统配置
MEMORY_CONFIG = {
    "api_url": os.getenv("MEMORY_API_URL", "http://172.16.154.251:21004"),
    "app_id": os.getenv("MEMORY_APP_ID", ""),
    "repo_id": os.getenv("MEMORY_REPO_ID", ""),
    "agent_id": os.getenv("MEMORY_AGENT_ID", "decision_agent"),
    "retrieval_top_n": 5,
    "retrieval_threshold": 0.25,  # 语义相似度阈值（越低召回越多）
}
