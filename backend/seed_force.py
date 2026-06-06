#!/usr/bin/env python3
"""샘플 데이터 강제 생성 (대화형 프롬프트 없음)"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
from app.models import Student, AttendanceRecord, DocumentSubmission, StudentParent, AttendanceType, AttendanceReason, ApprovalStatus

def create_sample_data_force():
    """샘플 데이터 강제 생성"""
    print("Initializing database...")
    init_db()

    db = SessionLocal()

    try:
        # 기존 데이터 확인
        existing_students = db.query(Student).count()
        if existing_students > 0:
            print(f"Database already has {existing_students} students.")
            print("Clearing existing data...")
            db.query(DocumentSubmission).delete()
            db.query(AttendanceRecord).delete()
            db.query(StudentParent).delete()
            db.query(Student).delete()
            db.commit()
            print("✅ Existing data cleared")

        # 샘플 학생 데이터 생성
        students = [
            Student(name="홍길동", student_number=1),
            Student(name="김철수", student_number=2),
            Student(name="이영희", student_number=3),
            Student(name="박민수", student_number=4),
            Student(name="주선", student_number=5),
        ]

        for student in students:
            db.add(student)

        db.commit()
        print(f"✅ Created {len(students)} students")

        # 학부모는 텔레그램 봇을 통해 자동 등록됩니다
        # 테스트 데이터에는 학부모를 추가하지 않습니다

        # 샘플 출결 데이터 생성
        today = datetime.now().date()
        attendance_records = []

        # 홍길동 - 질병 결석
        record1 = AttendanceRecord(
            student_id=students[0].id,
            date=today - timedelta(days=1),
            attendance_type=AttendanceType.ABSENT,
            attendance_reason=AttendanceReason.ILLNESS,
            approval_status=ApprovalStatus.APPROVED,
            original_message="홍길동 아파서 결석합니다",
        )
        attendance_records.append(record1)

        # 김철수 - 지각
        record2 = AttendanceRecord(
            student_id=students[1].id,
            date=today,
            attendance_type=AttendanceType.LATE,
            attendance_reason=AttendanceReason.UNAUTHORIZED,
            approval_status=ApprovalStatus.PENDING,
            original_message="김철수 늦잠 자서 지각",
        )
        attendance_records.append(record2)

        # 이영희 - 출석인정 결석 (체험학습)
        record3 = AttendanceRecord(
            student_id=students[2].id,
            date=today + timedelta(days=1),
            attendance_type=AttendanceType.ABSENT,
            attendance_reason=AttendanceReason.AUTHORIZED,
            approval_status=ApprovalStatus.PENDING,
            original_message="이영희 현장체험학습으로 결석",
        )
        attendance_records.append(record3)

        for record in attendance_records:
            db.add(record)

        db.commit()
        print(f"✅ Created {len(attendance_records)} attendance records")

        # 샘플 서류 제출 데이터 생성 (결석 기록에 대한 서류)
        document_submissions = []

        # 홍길동의 질병 결석 - 서류 미제출
        doc1 = DocumentSubmission(
            student_id=students[0].id,
            attendance_record_id=record1.id,
            date=today - timedelta(days=1),
            document_type="진단서",
            is_submitted=False,
        )
        document_submissions.append(doc1)

        # 이영희의 출석인정 결석 - 서류 미제출
        doc2 = DocumentSubmission(
            student_id=students[2].id,
            attendance_record_id=record3.id,
            date=today + timedelta(days=1),
            document_type="체험학습 신청서",
            is_submitted=False,
        )
        document_submissions.append(doc2)

        for doc in document_submissions:
            db.add(doc)

        db.commit()
        print(f"✅ Created {len(document_submissions)} document submissions")

        print("\n🎉 Sample data created successfully!")
        print(f"   Students: {len(students)}")
        print(f"   Attendance records: {len(attendance_records)}")
        print(f"   Document submissions: {len(document_submissions)}")
        print("\n💡 학부모는 텔레그램 봇으로 메시지를 보내면 자동으로 등록됩니다.")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data_force()
