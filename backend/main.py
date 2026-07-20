import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers.user_router import router as user_router
from routers.card_router import router as card_router
from routers.memory_router import router as memory_router
from routers.auth_router import router as auth_router
from routers.case_router import router as case_router

app = FastAPI(title="不纠结 - AI个性化决策助手", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(card_router)
app.include_router(memory_router)
app.include_router(case_router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"message": "不纠结 API is running", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
