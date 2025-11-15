import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import init_db
from .api.routes import students, attendance, documents, parents

# uploads 디렉토리 생성 (앱 시작 전)
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# FastAPI 앱 생성
app = FastAPI(
    title="출결 관리 시스템 API",
    description="텔레그램 봇과 Claude AI 기반 출결 관리 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(students.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(parents.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    """앱 시작 시 데이터베이스 초기화"""
    init_db()


# 정적 파일 서빙 (서류 사진) - startup 이후에 마운트되도록 보장
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def root():
    """API 루트"""
    return {
        "message": "출결 관리 시스템 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """헬스 체크"""
    return {"status": "healthy"}
