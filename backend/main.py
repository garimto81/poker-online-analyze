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
import os

# 개발/프로덕션 환경에 따른 CORS 설정
allowed_origins = [
    "http://localhost:4000",
    "http://localhost:4001", 
    "http://localhost:4002",
    "https://poker-analyzer-frontend.vercel.app",
    "https://*.vercel.app"
]

# 환경 변수로 추가 도메인 허용
if os.environ.get("FRONTEND_URL"):
    allowed_origins.append(os.environ.get("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
