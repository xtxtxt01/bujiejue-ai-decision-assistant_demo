from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import bcrypt
from database import get_db
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    nickname: str = ""
    mbti: str = ""
    decision_style: str = ""
    maximizer_tendency: str = ""
    values_ranking: list[str] = []
    life_stage: str = ""
    frequent_dilemma_types: list[str] = []
    self_intro: str = ""
    theme: str = "default"


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(req: RegisterRequest):
    conn = get_db()

    # 检查用户名是否已存在
    existing = conn.execute("SELECT uid FROM users WHERE username = ?", (req.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 生成 uid 和加密密码
    uid = str(uuid.uuid4())[:8]
    password_hash = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 插入用户
    from services.user_service import create_user
    create_user(
        uid=uid,
        username=req.username,
        password_hash=password_hash,
        nickname=req.nickname or req.username,
        mbti=req.mbti,
        decision_style=req.decision_style,
        maximizer_tendency=req.maximizer_tendency,
        values_ranking=req.values_ranking,
        life_stage=req.life_stage,
        frequent_dilemma_types=req.frequent_dilemma_types,
        self_intro=req.self_intro,
        theme=req.theme,
    )

    conn.close()
    return {"uid": uid, "username": req.username, "nickname": req.nickname or req.username}


@router.post("/login")
def login(req: LoginRequest):
    conn = get_db()
    user = conn.execute(
        "SELECT uid, username, nickname, password_hash, theme FROM users WHERE username = ?",
        (req.username,)
    ).fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 验证密码
    if not bcrypt.checkpw(req.password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return {
        "uid": user["uid"],
        "username": user["username"],
        "nickname": user["nickname"],
        "theme": user["theme"]
    }
