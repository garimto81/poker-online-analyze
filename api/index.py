"""
Vercel Serverless Functions를 위한 FastAPI 엔트리포인트
GitHub Pages에서도 사용 가능한 API 엔드포인트
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# 현재 파일의 상위 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from backend.app.api.endpoints import firebase_poker
except ImportError:
    # 대안 경로로 시도
    sys.path.append(os.path.join(parent_dir, 'backend'))
    from app.api.endpoints import firebase_poker

app = FastAPI(
    title="Poker Analyzer API",
    description="온라인 포커 데이터 분석 API",
    version="1.0.0"
)

# CORS 설정 - 더 관대한 설정으로 테스트 환경 지원
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://garimto81.github.io",
        "https://*.github.io",
        "http://localhost:4000",
        "http://localhost:3000",
        "https://poker-analyzer-frontend.vercel.app",
        "https://*.vercel.app",
        "*"  # 개발 중에는 모든 origin 허용
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Firebase API 라우터 포함
app.include_router(firebase_poker.router, prefix="/api/firebase", tags=["Firebase"])

@app.get("/")
async def root():
    return {
        "message": "Poker Analyzer API",
        "status": "online",
        "docs": "/docs",
        "github_pages": "https://garimto81.github.io/poker-online-analyze",
        "endpoints": {
            "current_ranking": "/api/firebase/current_ranking/",
            "all_sites_daily_stats": "/api/firebase/all_sites_daily_stats/",
            "crawl": "/api/firebase/crawl_and_save_data/"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "poker-analyzer-api"}

@app.get("/test")
async def test_endpoint():
    return {"message": "API is working!", "timestamp": "2025-01-30"}

# Vercel용 핸들러
handler = app