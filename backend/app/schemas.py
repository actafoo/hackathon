from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .models import AttendanceType, AttendanceReason, ApprovalStatus


# Student Schemas
class StudentBase(BaseModel):
    name: str
    student_number: int
    telegram_id: Optional[str] = None
    phone: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class Student(StudentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Student Parent Schemas
class StudentParentBase(BaseModel):
    student_id: int
    telegram_id: str
    parent_name: Optional[str] = None
    relation: Optional[str] = None


class StudentParentCreate(StudentParentBase):
    auto_registered: bool = False  # 수동 등록은 False


class StudentParentUpdate(BaseModel):
    parent_name: Optional[str] = None
    relation: Optional[str] = None
    is_active: Optional[bool] = None


class StudentParent(StudentParentBase):
    id: int
    is_active: bool
    auto_registered: bool
    first_contact_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Attendance Record Schemas
class AttendanceRecordBase(BaseModel):
    student_id: int
    date: datetime
    attendance_type: AttendanceType
    attendance_reason: AttendanceReason


class AttendanceRecordCreate(AttendanceRecordBase):
    original_message: Optional[str] = None


class AttendanceRecordUpdate(BaseModel):
    attendance_type: Optional[AttendanceType] = None
    attendance_reason: Optional[AttendanceReason] = None
    approval_status: Optional[ApprovalStatus] = None
    modified_by: Optional[str] = None
    modification_reason: Optional[str] = None


class AttendanceRecord(AttendanceRecordBase):
    id: int
    approval_status: ApprovalStatus
    original_message: Optional[str]
    modified_by: Optional[str]
    modified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Document Submission Schemas
class DocumentSubmissionBase(BaseModel):
    student_id: int
    date: datetime
    document_type: Optional[str] = None


class DocumentSubmissionCreate(DocumentSubmissionBase):
    attendance_record_id: Optional[int] = None


class DocumentSubmissionUpdate(BaseModel):
    is_submitted: Optional[bool] = None
    submitted_at: Optional[datetime] = None


class DocumentSubmission(DocumentSubmissionBase):
    id: int
    is_submitted: bool
    submitted_at: Optional[datetime]
    reminder_sent: bool
    reminder_sent_at: Optional[datetime]
    file_path: Optional[str] = None
    file_telegram_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# AI Extraction Schemas
class ExtractedAttendanceData(BaseModel):
    """Claude AI가 추출한 출결 데이터"""
    intent: str = Field(description="사용자 의도: create(출결등록), update(수정), cancel(취소)")
    student_name: Optional[str] = Field(default=None, description="학생 이름 (update/cancel 시 없을 수 있음)")
    date: Optional[str] = Field(default=None, description="시작 날짜 (YYYY-MM-DD 형식)")
    end_date: Optional[str] = Field(default=None, description="종료 날짜 (YYYY-MM-DD 형식, 기간인 경우)")
    attendance_type: Optional[str] = Field(default=None, description="출결 타입: 결석, 조퇴, 지각 중 하나")
    attendance_reason: Optional[str] = Field(default=None, description="출결 사유: 질병, 미인정, 출석인정 중 하나")
    confidence: float = Field(description="추출 신뢰도 (0.0 ~ 1.0)", ge=0.0, le=1.0)


class TelegramMessageResponse(BaseModel):
    """텔레그램 메시지 처리 응답"""
    success: bool
    message: str
    extracted_data: Optional[ExtractedAttendanceData] = None
    attendance_record_id: Optional[int] = None


# Dashboard Schemas
class MonthlyAttendanceRequest(BaseModel):
    year: int = Field(description="연도")
    month: int = Field(description="월", ge=1, le=12)


class DailyAttendanceCell(BaseModel):
    """대시보드 그리드의 각 셀"""
    student_id: int
    student_name: str
    student_number: int
    date: datetime
    attendance_type: Optional[AttendanceType] = None
    attendance_reason: Optional[AttendanceReason] = None
    approval_status: Optional[ApprovalStatus] = None
    document_submitted: bool = False
    record_id: Optional[int] = None
    original_message: Optional[str] = None


class MonthlyAttendanceGrid(BaseModel):
    """월별 출결 그리드 데이터"""
    year: int
    month: int
    students: list[Student]
    attendance_data: list[DailyAttendanceCell]
