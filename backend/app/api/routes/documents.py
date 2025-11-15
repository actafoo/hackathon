from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ...database import get_db
from ...models import DocumentSubmission, Student, StudentParent
from ...schemas import (
    DocumentSubmission as DocumentSubmissionSchema,
    DocumentSubmissionCreate,
    DocumentSubmissionUpdate
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=List[DocumentSubmissionSchema])
def get_document_submissions(
    skip: int = 0,
    limit: int = 100,
    student_id: int = None,
    is_submitted: bool = None,
    db: Session = Depends(get_db)
):
    """서류 제출 기록 조회"""
    query = db.query(DocumentSubmission)

    if student_id:
        query = query.filter(DocumentSubmission.student_id == student_id)
    if is_submitted is not None:
        query = query.filter(DocumentSubmission.is_submitted == is_submitted)

    submissions = query.order_by(DocumentSubmission.date.desc()).offset(skip).limit(limit).all()
    return submissions


@router.get("/unsubmitted", response_model=List[DocumentSubmissionSchema])
def get_unsubmitted_documents(db: Session = Depends(get_db)):
    """서류 미제출 목록 조회"""
    unsubmitted = db.query(DocumentSubmission).filter(
        DocumentSubmission.is_submitted == False
    ).order_by(DocumentSubmission.date.desc()).all()
    return unsubmitted


@router.post("/", response_model=DocumentSubmissionSchema)
def create_document_submission(submission: DocumentSubmissionCreate, db: Session = Depends(get_db)):
    """서류 제출 기록 생성"""
    # 학생 존재 확인
    student = db.query(Student).filter(Student.id == submission.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db_submission = DocumentSubmission(**submission.dict())
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission


@router.put("/{submission_id}", response_model=DocumentSubmissionSchema)
def update_document_submission(
    submission_id: int,
    submission_update: DocumentSubmissionUpdate,
    db: Session = Depends(get_db)
):
    """서류 제출 기록 수정"""
    submission = db.query(DocumentSubmission).filter(DocumentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Document submission not found")

    update_data = submission_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(submission, field, value)

    # 제출 시간 자동 기록
    if submission_update.is_submitted and not submission.submitted_at:
        submission.submitted_at = datetime.utcnow()

    db.commit()
    db.refresh(submission)
    return submission


@router.post("/{submission_id}/mark-submitted")
def mark_document_submitted(submission_id: int, db: Session = Depends(get_db)):
    """서류 제출 완료 표시"""
    submission = db.query(DocumentSubmission).filter(DocumentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Document submission not found")

    submission.is_submitted = True
    submission.submitted_at = datetime.utcnow()

    db.commit()
    return {"message": "Document marked as submitted", "submission_id": submission_id}


@router.post("/send-reminder/{student_id}")
async def send_individual_reminder(student_id: int, db: Session = Depends(get_db)):
    """특정 학생의 모든 학부모에게 개별 독려 메시지 발송"""
    import telegram
    import os

    # 학생 정보 조회
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")

    # 학부모 목록 조회 (활성화된 학부모만)
    parents = db.query(StudentParent).filter(
        StudentParent.student_id == student_id,
        StudentParent.is_active == True
    ).all()

    if not parents:
        raise HTTPException(
            status_code=400,
            detail=f"{student.name} 학생의 등록된 학부모가 없습니다"
        )

    # 미제출 서류 확인
    unsubmitted = db.query(DocumentSubmission).filter(
        DocumentSubmission.student_id == student_id,
        DocumentSubmission.is_submitted == False
    ).all()

    unsubmitted_count = len(unsubmitted)

    if unsubmitted_count == 0:
        return {
            "message": "제출할 서류가 없습니다",
            "sent": False,
            "student_name": student.name
        }

    # 메시지 생성
    message = f"""📝 {student.name} 학생 학부모님 안녕하세요!

미제출 서류 {unsubmitted_count}건이 있습니다.

"""

    for doc in unsubmitted[:5]:  # 최대 5건만 표시
        message += f"• {doc.date.strftime('%Y-%m-%d')} - {doc.document_type or '출결 서류'}\n"

    if unsubmitted_count > 5:
        message += f"• 외 {unsubmitted_count - 5}건\n"

    message += "\n빠른 시일 내에 제출 부탁드립니다."

    # 텔레그램 봇 직접 사용
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    bot = telegram.Bot(token=bot_token)
    sent_count = 0
    failed_parents = []

    for parent in parents:
        try:
            await bot.send_message(
                chat_id=parent.telegram_id,
                text=message
            )
            sent_count += 1
        except Exception as e:
            failed_parents.append(parent.id)
            print(f"❌ 발송 실패 (parent_id={parent.id}): {e}")

    # 발송 기록 업데이트
    if sent_count > 0:
        for doc in unsubmitted:
            doc.reminder_sent = True
            doc.reminder_sent_at = datetime.utcnow()
        db.commit()

    return {
        "message": f"독려 메시지 발송 완료",
        "student_name": student.name,
        "parents_count": len(parents),
        "sent_count": sent_count,
        "failed_count": len(failed_parents),
        "unsubmitted_count": unsubmitted_count
    }


@router.post("/send-reminders")
async def send_reminders_to_unsubmitted(db: Session = Depends(get_db)):
    """서류 미제출 학생 전체에게 독려 메시지 일괄 발송"""
    import telegram
    import os

    # 서류 미제출 학생 목록 조회 (중복 제거)
    unsubmitted_students = db.query(DocumentSubmission.student_id).filter(
        DocumentSubmission.is_submitted == False
    ).distinct().all()

    if not unsubmitted_students:
        return {"message": "서류 미제출 학생이 없습니다", "count": 0}

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    bot = telegram.Bot(token=bot_token)
    sent_count = 0
    failed_count = 0
    total_messages = 0

    for (student_id,) in unsubmitted_students:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            failed_count += 1
            continue

        # 학부모 목록 조회
        parents = db.query(StudentParent).filter(
            StudentParent.student_id == student_id,
            StudentParent.is_active == True
        ).all()

        if not parents:
            failed_count += 1
            continue

        # 미제출 서류 확인
        unsubmitted = db.query(DocumentSubmission).filter(
            DocumentSubmission.student_id == student_id,
            DocumentSubmission.is_submitted == False
        ).all()

        # 메시지 생성
        message = f"""📝 {student.name} 학생 학부모님 안녕하세요!

미제출 서류 {len(unsubmitted)}건이 있습니다.

"""
        for doc in unsubmitted[:5]:
            message += f"• {doc.date.strftime('%Y-%m-%d')} - {doc.document_type or '출결 서류'}\n"

        if len(unsubmitted) > 5:
            message += f"• 외 {len(unsubmitted) - 5}건\n"

        message += "\n빠른 시일 내에 제출 부탁드립니다."

        # 모든 학부모에게 발송
        student_sent = False
        for parent in parents:
            try:
                await bot.send_message(
                    chat_id=parent.telegram_id,
                    text=message
                )
                student_sent = True
                total_messages += 1
            except Exception as e:
                print(f"❌ 발송 실패: student={student.name}, parent_id={parent.id}, error={e}")

        if student_sent:
            # 발송 기록 업데이트
            for doc in unsubmitted:
                doc.reminder_sent = True
                doc.reminder_sent_at = datetime.utcnow()
            sent_count += 1
        else:
            failed_count += 1

    db.commit()

    return {
        "message": f"독려 메시지 일괄 발송 완료",
        "sent_count": sent_count,
        "failed_count": failed_count,
        "total_messages": total_messages
    }


@router.delete("/{submission_id}")
def delete_document_submission(submission_id: int, db: Session = Depends(get_db)):
    """서류 제출 기록 삭제"""
    submission = db.query(DocumentSubmission).filter(DocumentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Document submission not found")

    db.delete(submission)
    db.commit()
    return {"message": "Document submission deleted"}
