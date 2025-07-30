"""
Vercel Serverless Functions를 위한 FastAPI 엔트리포인트
GitHub Pages에서도 사용 가능한 API 엔드포인트
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# 백엔드 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app.api.endpoints import firebase_poker

app = FastAPI(
    title="Poker Analyzer API",
    description="온라인 포커 데이터 분석 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://garimto81.github.io",
        "https://*.github.io",
        "http://localhost:4000",
        "https://poker-analyzer-frontend.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase API 라우터 포함
app.include_router(firebase_poker.router, prefix="/api/firebase", tags=["Firebase"])

@app.get("/")
async def root():
    return {
        "message": "Poker Analyzer API",
        "docs": "/docs",
        "github_pages": "https://garimto81.github.io/poker-online-analyze"
    }

# Vercel용 핸들러
handler = app