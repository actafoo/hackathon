from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...database import get_db
from ...models import StudentParent, Student
from ...schemas import (
    StudentParent as StudentParentSchema,
    StudentParentCreate,
    StudentParentUpdate
)

router = APIRouter(prefix="/parents", tags=["parents"])


@router.get("/student/{student_id}", response_model=List[StudentParentSchema])
def get_student_parents(student_id: int, db: Session = Depends(get_db)):
    """특정 학생의 학부모 목록 조회"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")

    parents = db.query(StudentParent).filter(
        StudentParent.student_id == student_id
    ).all()

    return parents


@router.post("/", response_model=StudentParentSchema)
def create_parent(parent: StudentParentCreate, db: Session = Depends(get_db)):
    """학부모 수동 등록 (교사)"""
    # 학생 존재 확인
    student = db.query(Student).filter(Student.id == parent.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")

    # 중복 확인
    existing = db.query(StudentParent).filter(
        StudentParent.student_id == parent.student_id,
        StudentParent.telegram_id == parent.telegram_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="이미 등록된 학부모입니다")

    # 새 학부모 등록
    db_parent = StudentParent(**parent.dict())
    db.add(db_parent)
    db.commit()
    db.refresh(db_parent)

    return db_parent


@router.put("/{parent_id}", response_model=StudentParentSchema)
def update_parent(
    parent_id: int,
    parent_update: StudentParentUpdate,
    db: Session = Depends(get_db)
):
    """학부모 정보 수정 (교사)"""
    parent = db.query(StudentParent).filter(StudentParent.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="학부모를 찾을 수 없습니다")

    # 수정 사항 적용
    update_data = parent_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(parent, field, value)

    db.commit()
    db.refresh(parent)

    return parent


@router.delete("/{parent_id}")
def delete_parent(parent_id: int, db: Session = Depends(get_db)):
    """학부모 삭제 (교사)"""
    parent = db.query(StudentParent).filter(StudentParent.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="학부모를 찾을 수 없습니다")

    db.delete(parent)
    db.commit()

    return {"message": "학부모가 삭제되었습니다", "parent_id": parent_id}


@router.post("/{parent_id}/toggle-active")
def toggle_parent_active(parent_id: int, db: Session = Depends(get_db)):
    """학부모 활성/비활성 토글 (삭제 대신 비활성화)"""
    parent = db.query(StudentParent).filter(StudentParent.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="학부모를 찾을 수 없습니다")

    parent.is_active = not parent.is_active
    db.commit()
    db.refresh(parent)

    status = "활성화" if parent.is_active else "비활성화"
    return {
        "message": f"학부모가 {status}되었습니다",
        "parent_id": parent_id,
        "is_active": parent.is_active
    }
