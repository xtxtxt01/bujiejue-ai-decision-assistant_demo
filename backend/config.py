import os

LLM_CONFIG = {
    "api_url": "https://maas-api.cn-huabei-1.xf-yun.com/v2/chat/completions",
    "models": {
        "main": {"id": "xopdeepseekv4flash", "key": "b27ea9b866bd98d431ae63c0c87fd152:Y2IwMTAwNTcwOTVkZTAyMTMyYzgwYWZj"},
        "fast": {"id": "xop3qwen4b", "key": "7a456a065971dde32efd85aa8c2d354c:MzRlYTQ0MjJiNDA3NzYyMTI3MDIwZjQ1"},
    },
    "temperature": 0.7,
    "max_tokens": 2048,
}

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")

# Memosyne 记忆系统配置
MEMORY_CONFIG = {
    "api_url": "http://172.16.154.251:21004",
    "app_id": "5f2bb768",
    "repo_id": "demo_repo",
    "agent_id": "decision_agent",
    "retrieval_top_n": 5,
    "retrieval_threshold": 0.25,  # 语义相似度阈值（越低召回越多）
}
