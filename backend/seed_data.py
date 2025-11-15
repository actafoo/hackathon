#!/usr/bin/env python3
"""샘플 데이터 생성 스크립트"""

import sys
import os
from datetime import datetime, timedelta

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
from app.models import Student, AttendanceRecord, DocumentSubmission, AttendanceType, AttendanceReason, ApprovalStatus


def create_sample_data():
    """샘플 데이터 생성"""
    print("Initializing database...")
    init_db()

    db = SessionLocal()

    try:
        # 기존 데이터 확인
        existing_students = db.query(Student).count()
        if existing_students > 0:
            print(f"Database already has {existing_students} students.")
            if input("Clear existing data and create new? (y/N): ").lower() != 'y':
                return
            # 데이터 삭제
            db.query(DocumentSubmission).delete()
            db.query(AttendanceRecord).delete()
            db.query(Student).delete()
            db.commit()

        # 샘플 학생 생성
        students_data = [
            {"name": "홍길동", "student_number": 1, "telegram_id": "user001"},
            {"name": "김철수", "student_number": 2, "telegram_id": "user002"},
            {"name": "이영희", "student_number": 3, "telegram_id": "user003"},
            {"name": "박민수", "student_number": 4, "telegram_id": "user004"},
            {"name": "최수진", "student_number": 5, "telegram_id": "user005"},
            {"name": "정하늘", "student_number": 6, "telegram_id": "user006"},
            {"name": "강바다", "student_number": 7, "telegram_id": "user007"},
            {"name": "윤별", "student_number": 8, "telegram_id": "user008"},
            {"name": "임구름", "student_number": 9, "telegram_id": "user009"},
            {"name": "한솔", "student_number": 10, "telegram_id": "user010"},
        ]

        students = []
        for data in students_data:
            student = Student(**data)
            db.add(student)
            students.append(student)

        db.commit()
        print(f"Created {len(students)} students")

        # 샘플 출결 기록 생성 (이번 달)
        today = datetime.now()
        current_month = today.replace(day=1)

        attendance_samples = [
            # 질병 관련
            (students[0], 5, AttendanceType.ABSENT, AttendanceReason.ILLNESS, "감기로 결석합니다"),
            (students[1], 7, AttendanceType.LATE, AttendanceReason.ILLNESS, "병원 다녀오느라 지각"),
            (students[2], 10, AttendanceType.EARLY_LEAVE, AttendanceReason.ILLNESS, "배탈나서 조퇴"),

            # 미인정
            (students[3], 8, AttendanceType.LATE, AttendanceReason.UNAUTHORIZED, "늦잠"),
            (students[4], 12, AttendanceType.ABSENT, AttendanceReason.UNAUTHORIZED, "개인 사정"),

            # 출석인정
            (students[5], 14, AttendanceType.ABSENT, AttendanceReason.AUTHORIZED, "현장체험학습"),
            (students[6], 14, AttendanceType.ABSENT, AttendanceReason.AUTHORIZED, "가족여행"),
            (students[7], 18, AttendanceType.LATE, AttendanceReason.AUTHORIZED, "공적 행사 참여"),

            # 추가 샘플
            (students[8], 20, AttendanceType.ABSENT, AttendanceReason.ILLNESS, "독감"),
            (students[9], 22, AttendanceType.EARLY_LEAVE, AttendanceReason.AUTHORIZED, "조퇴"),
        ]

        records = []
        for student, day, att_type, att_reason, message in attendance_samples:
            record = AttendanceRecord(
                student_id=student.id,
                date=current_month.replace(day=day),
                attendance_type=att_type,
                attendance_reason=att_reason,
                approval_status=ApprovalStatus.PENDING,
                original_message=message
            )
            db.add(record)
            records.append(record)

        db.commit()
        print(f"Created {len(records)} attendance records")

        # 샘플 서류 제출 기록 생성
        doc_submissions = []
        for i, record in enumerate(records[:5]):
            doc = DocumentSubmission(
                student_id=record.student_id,
                attendance_record_id=record.id,
                date=record.date,
                is_submitted=(i % 2 == 0),  # 일부만 제출된 상태
                document_type="진단서" if record.attendance_reason == AttendanceReason.ILLNESS else "증빙서류"
            )
            db.add(doc)
            doc_submissions.append(doc)

        db.commit()
        print(f"Created {len(doc_submissions)} document submissions")

        print("\n✅ Sample data created successfully!")
        print("\nSample Students:")
        for student in students:
            print(f"  - {student.student_number}. {student.name}")

        print("\nSample Attendance Records:")
        for record in records:
            student = next(s for s in students if s.id == record.student_id)
            print(f"  - {student.name}: {record.date.strftime('%m/%d')} {record.attendance_type.value} ({record.attendance_reason.value})")

    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()
