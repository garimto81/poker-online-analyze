from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import poker, firebase_poker
from app.database.database import engine, Base

# 데이터베이스 테이블 생성 (PostgreSQL 사용 시)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Poker Online Analyze API",
    description="온라인 포커 데이터 수집 및 분석 API",
    version="1.0.0"
)

# CORS 설정 - 프론트엔드와의 통신을 위해
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://localhost:4001", "http://localhost:4002"],  # 프론트엔드 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(poker.router, prefix="/api", tags=["PostgreSQL-based"])
app.include_router(firebase_poker.router, prefix="/api/firebase", tags=["Firebase-based"])

@app.get("/")
async def read_root():
    return {
        "message": "Welcome to Poker Online Analyze Backend!",
        "docs": "/docs",
        "firebase_api": "/api/firebase",
        "postgresql_api": "/api"
    }
