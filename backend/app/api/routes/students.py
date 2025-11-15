from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...database import get_db
from ...models import Student
from ...schemas import Student as StudentSchema, StudentCreate

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/", response_model=List[StudentSchema])
def get_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """모든 학생 목록 조회 (출석번호순)"""
    students = db.query(Student).order_by(Student.student_number).offset(skip).limit(limit).all()
    return students


@router.get("/{student_id}", response_model=StudentSchema)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """특정 학생 조회"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("/", response_model=StudentSchema)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """새 학생 등록"""
    # 중복 체크
    existing = db.query(Student).filter(Student.student_number == student.student_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student number already exists")

    # 빈 문자열을 None으로 변환 (UNIQUE 제약조건 회피)
    student_data = student.dict()
    if student_data.get('telegram_id') == '':
        student_data['telegram_id'] = None
    if student_data.get('phone') == '':
        student_data['phone'] = None

    db_student = Student(**student_data)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """학생 삭제"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}
