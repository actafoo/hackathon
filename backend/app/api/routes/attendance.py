from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, extract
from typing import List
from datetime import datetime
from ...database import get_db
from ...models import AttendanceRecord, Student, ApprovalStatus, DocumentSubmission, StudentParent
from ...schemas import (
    AttendanceRecord as AttendanceRecordSchema,
    AttendanceRecordCreate,
    AttendanceRecordUpdate,
    MonthlyAttendanceRequest,
    MonthlyAttendanceGrid,
    DailyAttendanceCell
)

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("/", response_model=List[AttendanceRecordSchema])
def get_attendance_records(
    skip: int = 0,
    limit: int = 100,
    student_id: int = None,
    approval_status: ApprovalStatus = None,
    db: Session = Depends(get_db)
):
    """출결 기록 조회"""
    query = db.query(AttendanceRecord)

    if student_id:
        query = query.filter(AttendanceRecord.student_id == student_id)
    if approval_status:
        query = query.filter(AttendanceRecord.approval_status == approval_status)

    records = query.order_by(AttendanceRecord.date.desc()).offset(skip).limit(limit).all()
    return records


@router.get("/{record_id}", response_model=AttendanceRecordSchema)
def get_attendance_record(record_id: int, db: Session = Depends(get_db)):
    """특정 출결 기록 조회"""
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record


@router.post("/", response_model=AttendanceRecordSchema)
def create_attendance_record(record: AttendanceRecordCreate, db: Session = Depends(get_db)):
    """출결 기록 생성"""
    # 학생 존재 확인
    student = db.query(Student).filter(Student.id == record.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db_record = AttendanceRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.put("/{record_id}", response_model=AttendanceRecordSchema)
def update_attendance_record(
    record_id: int,
    record_update: AttendanceRecordUpdate,
    db: Session = Depends(get_db)
):
    """출결 기록 수정 (교사)"""
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    # 수정 사항 적용
    update_data = record_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    # 수정 시간 기록
    if record_update.modified_by:
        record.modified_at = datetime.utcnow()

    db.commit()
    db.refresh(record)
    return record


@router.post("/{record_id}/approve")
def approve_attendance_record(record_id: int, teacher_name: str, db: Session = Depends(get_db)):
    """출결 기록 승인"""
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    record.approval_status = ApprovalStatus.APPROVED
    record.modified_by = teacher_name
    record.modified_at = datetime.utcnow()

    db.commit()
    return {"message": "Attendance record approved", "record_id": record_id}


@router.post("/{record_id}/reject")
async def reject_attendance_record(
    record_id: int,
    teacher_name: str,
    reason: str = None,
    db: Session = Depends(get_db)
):
    """출결 기록 거부 (학부모에게 텔레그램 알림 발송)"""
    from ...services.telegram_bot import AttendanceTelegramBot
    import telegram
    import os

    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    record.approval_status = ApprovalStatus.REJECTED
    record.modified_by = teacher_name
    record.modified_at = datetime.utcnow()
    if reason:
        record.modification_reason = reason

    db.commit()

    # 학부모에게 텔레그램 알림 발송
    student = db.query(Student).filter(Student.id == record.student_id).first()
    if student:
        parents = db.query(StudentParent).filter(
            StudentParent.student_id == student.id,
            StudentParent.is_active == True
        ).all()

        if parents:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            bot = telegram.Bot(token=bot_token)

            rejection_message = f"""❌ {student.name} 학생 학부모님께,

{record.date.strftime('%Y년 %m월 %d일')}자 출결 기록이 거부되었습니다.

📝 출결 내용: {record.attendance_type.value} - {record.attendance_reason.value}
👨‍🏫 담당 교사: {teacher_name}
"""

            if reason:
                rejection_message += f"\n📋 거부 사유:\n{reason}\n"

            rejection_message += "\n다시 확인하시고 재제출 또는 문의 부탁드립니다."

            for parent in parents:
                try:
                    await bot.send_message(
                        chat_id=parent.telegram_id,
                        text=rejection_message
                    )
                except Exception as e:
                    print(f"텔레그램 알림 발송 실패 (parent_id={parent.id}): {e}")

    return {
        "message": "Attendance record rejected",
        "record_id": record_id,
        "notification_sent": len(parents) if student and parents else 0
    }


@router.delete("/{record_id}")
def delete_attendance_record(record_id: int, db: Session = Depends(get_db)):
    """출결 기록 삭제"""
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    db.delete(record)
    db.commit()
    return {"message": "Attendance record deleted"}


@router.post("/monthly-grid", response_model=MonthlyAttendanceGrid)
def get_monthly_attendance_grid(request: MonthlyAttendanceRequest, db: Session = Depends(get_db)):
    """월별 출결 그리드 데이터 조회"""
    # 모든 학생 조회 (출석번호순)
    students = db.query(Student).order_by(Student.student_number).all()

    # 해당 월의 출결 기록 조회
    records = db.query(AttendanceRecord).filter(
        and_(
            extract('year', AttendanceRecord.date) == request.year,
            extract('month', AttendanceRecord.date) == request.month
        )
    ).all()

    # 서류 제출 기록 조회
    documents = db.query(DocumentSubmission).filter(
        and_(
            extract('year', DocumentSubmission.date) == request.year,
            extract('month', DocumentSubmission.date) == request.month
        )
    ).all()

    # 그리드 데이터 구성
    attendance_data = []
    for student in students:
        # 학생별 출결 기록
        student_records = [r for r in records if r.student_id == student.id]
        student_documents = [d for d in documents if d.student_id == student.id]

        for record in student_records:
            # 서류 제출 여부 확인
            doc_submitted = any(
                d.attendance_record_id == record.id and d.is_submitted
                for d in student_documents
            )

            cell = DailyAttendanceCell(
                student_id=student.id,
                student_name=student.name,
                student_number=student.student_number,
                date=record.date,
                attendance_type=record.attendance_type,
                attendance_reason=record.attendance_reason,
                approval_status=record.approval_status,
                document_submitted=doc_submitted,
                record_id=record.id,
                original_message=record.original_message
            )
            attendance_data.append(cell)

    return MonthlyAttendanceGrid(
        year=request.year,
        month=request.month,
        students=students,
        attendance_data=attendance_data
    )
