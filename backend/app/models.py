from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class AttendanceType(str, enum.Enum):
    """출결 타입"""
    ABSENT = "결석"
    EARLY_LEAVE = "조퇴"
    LATE = "지각"


class AttendanceReason(str, enum.Enum):
    """출결 사유"""
    ILLNESS = "질병"
    UNAUTHORIZED = "미인정"
    AUTHORIZED = "출석인정"


class ApprovalStatus(str, enum.Enum):
    """승인 상태"""
    PENDING = "대기"
    APPROVED = "승인"
    REJECTED = "거부"
    MODIFIED = "수정됨"


class Student(Base):
    """학생 정보"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    student_number = Column(Integer, nullable=False, unique=True, index=True)  # 출석번호
    telegram_id = Column(String, unique=True, index=True)  # 텔레그램 사용자 ID (deprecated - 학부모는 StudentParent 테이블 사용)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="student")
    document_submissions = relationship("DocumentSubmission", back_populates="student")
    parents = relationship("StudentParent", back_populates="student", cascade="all, delete-orphan")


class StudentParent(Base):
    """학생-학부모 연결 테이블 (한 학생에 여러 학부모 가능)"""
    __tablename__ = "student_parents"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    telegram_id = Column(String, nullable=False, index=True)  # 학부모 텔레그램 ID
    parent_name = Column(String)  # 학부모 이름 (선택)
    relation = Column(String)  # 관계: 부, 모, 조부모 등 (선택)
    is_active = Column(Boolean, default=True)  # 활성 상태 (교사가 비활성화 가능)
    auto_registered = Column(Boolean, default=True)  # 자동 등록 여부
    first_contact_at = Column(DateTime, default=datetime.utcnow)  # 최초 등록일
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="parents")


class AttendanceRecord(Base):
    """출결 기록"""
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)

    # 출결 상태 (9가지 조합)
    attendance_type = Column(Enum(AttendanceType), nullable=False)  # 결석/조퇴/지각
    attendance_reason = Column(Enum(AttendanceReason), nullable=False)  # 질병/미인정/출석인정

    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)

    # 추출된 원본 정보
    original_message = Column(Text)  # 텔레그램 원본 메시지
    extraction_log = Column(Text)  # AI 추출 로그

    # 수정 정보
    modified_by = Column(String)  # 수정한 교사
    modified_at = Column(DateTime)
    modification_reason = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="attendance_records")


class DocumentSubmission(Base):
    """서류 제출 기록"""
    __tablename__ = "document_submissions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    attendance_record_id = Column(Integer, ForeignKey("attendance_records.id"))
    date = Column(DateTime, nullable=False, index=True)
    is_submitted = Column(Boolean, default=False)
    submitted_at = Column(DateTime)
    document_type = Column(String)  # 병원진단서, 공결신청서 등
    file_path = Column(String)  # 제출된 파일 경로 (사진 등)
    file_telegram_id = Column(String)  # 텔레그램 파일 ID

    # 독려 메시지 발송 기록
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="document_submissions")


class TelegramMessage(Base):
    """텔레그램 메시지 로그"""
    __tablename__ = "telegram_messages"

    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(String, nullable=False, index=True)
    message_text = Column(Text, nullable=False)
    extracted_data = Column(Text)  # JSON 형태로 저장
    extraction_success = Column(Boolean, default=False)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
