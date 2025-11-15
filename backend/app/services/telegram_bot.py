import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from .claude_parser import ClaudeMessageParser
from ..database import SessionLocal
from ..models import Student, AttendanceRecord, TelegramMessage, StudentParent, DocumentSubmission, AttendanceType, AttendanceReason, ApprovalStatus
import json

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class AttendanceTelegramBot:
    """출결 관리 텔레그램 봇"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        self.parser = ClaudeMessageParser()
        self.application = Application.builder().token(self.bot_token).build()

        # 핸들러 등록
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """봇 시작 명령"""
        await update.message.reply_text(
            "안녕하세요! 출결 관리 봇입니다. 📚\n\n"
            "간단히 이름과 상황만 알려주세요!\n\n"
            "📝 예시:\n"
            "• 홍길동 아파요\n"
            "• 김철수 늦습니다\n"
            "• 이영희 현장체험학습\n"
            "• 박민수 오늘 못 갑니다\n\n"
            "💡 자세한 안내는 /help"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 명령"""
        help_text = """📋 출결 관리 봇 사용법

**간단히 보내주세요!**
학생 이름과 상황만 알려주시면 AI가 알아서 파악합니다.

📝 **예시:**
• "홍길동 아파요" → 질병 결석
• "김철수 늦습니다" → 지각
• "이영희 현장체험학습" → 출석인정 결석
• "박민수 오늘 병원 가요" → 질병 결석
• "최수진 조퇴합니다" → 조퇴
• "정하늘 못 갑니다" → 결석

📷 **서류 제출:**
• 진단서, 확인서 등을 사진으로 찍어 보내주세요
• 가장 최근 미제출 서류에 자동으로 등록됩니다

💡 **팁:**
- 날짜 생략 시 → 오늘로 처리
- "오늘", "내일" 등 사용 가능
- 맥락으로 출결 사유 자동 판단

🔹 **출결 종류:**
결석, 지각, 조퇴

🔹 **출결 사유:**
• 질병: 아프다, 병원, 감기 등
• 출석인정: 현장체험학습, 가족여행 등
• 미인정: 늦잠, 개인 사정 등
"""
        await update.message.reply_text(help_text)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """사진 메시지 처리 (서류 제출)"""
        user = update.effective_user
        telegram_user_id = str(user.id)

        logger.info(f"Received photo from {telegram_user_id}")

        db = SessionLocal()
        try:
            # 이 telegram_id로 등록된 학생의 학부모인지 확인
            parent = db.query(StudentParent).filter(
                StudentParent.telegram_id == telegram_user_id,
                StudentParent.is_active == True
            ).first()

            if not parent:
                await update.message.reply_text(
                    "등록되지 않은 사용자입니다.\n"
                    "먼저 출결 메시지를 보내서 학부모로 등록되어야 합니다."
                )
                return

            student = db.query(Student).filter(Student.id == parent.student_id).first()

            # 가장 최근 미제출 서류 찾기
            unsubmitted_doc = db.query(DocumentSubmission).filter(
                DocumentSubmission.student_id == student.id,
                DocumentSubmission.is_submitted == False
            ).order_by(DocumentSubmission.date.desc()).first()

            if not unsubmitted_doc:
                await update.message.reply_text(
                    f"{student.name} 학생의 미제출 서류가 없습니다."
                )
                return

            # 사진 파일 정보 저장
            photo = update.message.photo[-1]  # 가장 큰 크기의 사진
            file_telegram_id = photo.file_id

            # 실제 파일 다운로드 및 저장
            file = await context.bot.get_file(file_telegram_id)
            file_name = f"{student.id}_{int(datetime.utcnow().timestamp())}.jpg"
            file_path = f"uploads/{file_name}"
            await file.download_to_drive(file_path)

            # 서류 제출 완료 처리
            unsubmitted_doc.is_submitted = True
            unsubmitted_doc.submitted_at = datetime.utcnow()
            unsubmitted_doc.file_telegram_id = file_telegram_id
            unsubmitted_doc.file_path = file_name  # 파일명만 저장 (uploads/ 제외)

            db.commit()

            await update.message.reply_text(
                f"✅ {student.name} 학생의 서류가 접수되었습니다!\n\n"
                f"📅 날짜: {unsubmitted_doc.date.strftime('%Y-%m-%d')}\n"
                f"📋 서류 종류: {unsubmitted_doc.document_type or '출결 서류'}\n\n"
                f"교사 확인 후 최종 승인됩니다."
            )

            logger.info(f"Document submitted: student={student.name}, doc_id={unsubmitted_doc.id}")

        except Exception as e:
            logger.error(f"Error processing photo: {e}", exc_info=True)
            await update.message.reply_text(
                "사진 처리 중 오류가 발생했습니다.\n"
                "잠시 후 다시 시도해주세요."
            )
        finally:
            db.close()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일반 메시지 처리"""
        user = update.effective_user
        message_text = update.message.text

        logger.info(f"Received message from {user.id}: {message_text}")

        db = SessionLocal()
        try:
            # Claude AI로 메시지 파싱
            extracted_data, error = self.parser.parse_attendance_message(message_text)

            # 텔레그램 메시지 로그 저장
            telegram_message = TelegramMessage(
                telegram_user_id=str(user.id),
                message_text=message_text,
                extracted_data=json.dumps(extracted_data.dict()) if extracted_data else None,
                extraction_success=extracted_data is not None,
                error_message=error
            )
            db.add(telegram_message)
            db.commit()

            if error or not extracted_data:
                # 추출 실패 - 재요청 메시지 전송
                clarification = self.parser.generate_clarification_message(message_text, error or "알 수 없는 오류")
                await update.message.reply_text(clarification)
                return

            # 학생 찾기 로직
            student = None
            telegram_user_id = str(user.id)

            # 1. 메시지에서 학생 이름이 추출된 경우
            if extracted_data.student_name:
                student_name = extracted_data.student_name.replace("이", "").strip()  # "길동이" -> "길동"

                # 1-1. 전체 이름으로 찾기
                student = db.query(Student).filter(Student.name == student_name).first()

                # 1-2. 이름에 포함되는지 확인 (부분 매칭)
                if not student:
                    student = db.query(Student).filter(Student.name.contains(student_name)).first()

                # 1-3. 이름이 포함되어 있는지 역으로 확인 ("홍길동"에서 "길동" 찾기)
                if not student:
                    students = db.query(Student).all()
                    for s in students:
                        if student_name in s.name or s.name.endswith(student_name):
                            student = s
                            break

            # 2. 메시지에서 학생 이름을 찾을 수 없는 경우, telegram_user_id로 학부모 찾기
            if not student:
                parent = db.query(StudentParent).filter(
                    StudentParent.telegram_id == telegram_user_id,
                    StudentParent.is_active == True
                ).first()

                if parent:
                    student = db.query(Student).filter(Student.id == parent.student_id).first()
                    logger.info(f"📌 telegram_user_id로 학생 찾음: telegram_id={telegram_user_id}, student={student.name if student else None}")

            # 3. 여전히 학생을 찾을 수 없는 경우
            if not student:
                error_name = extracted_data.student_name if extracted_data.student_name else "학생"
                await update.message.reply_text(
                    f"'{error_name}' 학생을 찾을 수 없습니다.\n"
                    f"등록된 학생 이름을 정확히 입력해주세요."
                )
                return

            # 📌 학부모 자동 등록
            self._register_parent_if_new(db, student.id, str(user.id))

            # Intent에 따라 분기 처리
            intent = extracted_data.intent

            if intent == "cancel":
                # 취소 처리: 가장 최근 출결 기록 삭제
                await self._handle_cancel(db, student, message_text, update)
                return
            elif intent == "update":
                # 수정 처리: 가장 최근 출결 기록 수정
                await self._handle_update(db, student, extracted_data, message_text, update)
                return
            # intent == "create"인 경우 아래 기존 로직 실행

            # 출결 타입 매핑
            attendance_type_map = {
                "결석": AttendanceType.ABSENT,
                "조퇴": AttendanceType.EARLY_LEAVE,
                "지각": AttendanceType.LATE
            }

            # 출결 사유 매핑
            attendance_reason_map = {
                "질병": AttendanceReason.ILLNESS,
                "미인정": AttendanceReason.UNAUTHORIZED,
                "출석인정": AttendanceReason.AUTHORIZED
            }

            # 날짜 범위 처리
            from datetime import timedelta
            start_date = datetime.fromisoformat(extracted_data.date)
            dates_to_process = [start_date]

            # end_date가 있으면 범위 내 모든 날짜 생성
            if extracted_data.end_date:
                end_date = datetime.fromisoformat(extracted_data.end_date)
                current_date = start_date
                while current_date <= end_date:
                    if current_date != start_date:  # 시작일은 이미 추가됨
                        dates_to_process.append(current_date)
                    current_date += timedelta(days=1)

            # 각 날짜에 대해 출결 기록 생성
            created_records = []
            for record_date in dates_to_process:
                attendance_record = AttendanceRecord(
                    student_id=student.id,
                    date=record_date,
                    attendance_type=attendance_type_map[extracted_data.attendance_type],
                    attendance_reason=attendance_reason_map[extracted_data.attendance_reason],
                    approval_status=ApprovalStatus.PENDING,
                    original_message=message_text,
                    extraction_log=json.dumps(extracted_data.dict(), ensure_ascii=False)
                )

                db.add(attendance_record)
                db.commit()
                db.refresh(attendance_record)
                created_records.append(attendance_record)

                # 서류 제출이 필요한 경우 자동으로 서류 제출 기록 생성
                # 질병 결석, 출석인정 결석의 경우만 서류 필요 (지각, 조퇴는 제외)
                if (attendance_record.attendance_type == AttendanceType.ABSENT and
                    attendance_record.attendance_reason in [AttendanceReason.ILLNESS, AttendanceReason.AUTHORIZED]):
                    from ..models import DocumentSubmission

                    # 서류 타입 결정
                    document_type = None
                    if attendance_record.attendance_reason == AttendanceReason.ILLNESS:
                        document_type = "병원 진단서/소견서"
                    elif attendance_record.attendance_reason == AttendanceReason.AUTHORIZED:
                        document_type = "출석인정 관련 서류"

                    # 서류 제출 기록 생성
                    doc_submission = DocumentSubmission(
                        student_id=student.id,
                        attendance_record_id=attendance_record.id,
                        date=attendance_record.date,
                        is_submitted=False,
                        document_type=document_type
                    )
                    db.add(doc_submission)
                    db.commit()
                    logger.info(f"📄 서류 제출 기록 생성: student={student.name}, date={record_date.date()}, type={document_type}")

            # 성공 메시지 전송
            if len(dates_to_process) > 1:
                # 기간인 경우
                success_message = (
                    f"✅ 출결 정보가 접수되었습니다!\n\n"
                    f"👤 학생: {extracted_data.student_name}\n"
                    f"📅 기간: {extracted_data.date} ~ {extracted_data.end_date} ({len(dates_to_process)}일)\n"
                    f"📝 출결 타입: {extracted_data.attendance_type}\n"
                    f"📋 사유: {extracted_data.attendance_reason}\n\n"
                    f"교사 승인 대기 중입니다."
                )
            else:
                # 단일 날짜인 경우
                success_message = (
                    f"✅ 출결 정보가 접수되었습니다!\n\n"
                    f"👤 학생: {extracted_data.student_name}\n"
                    f"📅 날짜: {extracted_data.date}\n"
                    f"📝 출결 타입: {extracted_data.attendance_type}\n"
                    f"📋 사유: {extracted_data.attendance_reason}\n\n"
                    f"교사 승인 대기 중입니다."
                )

            # 서류 제출이 필요한 경우 안내 추가 (결석만)
            if any(r.attendance_type == AttendanceType.ABSENT and
                   r.attendance_reason in [AttendanceReason.ILLNESS, AttendanceReason.AUTHORIZED]
                   for r in created_records):
                doc_count = sum(1 for r in created_records
                               if r.attendance_type == AttendanceType.ABSENT and
                               r.attendance_reason in [AttendanceReason.ILLNESS, AttendanceReason.AUTHORIZED])
                success_message += f"\n\n📎 서류 제출이 필요합니다! (총 {doc_count}건)\n서류 사진을 촬영하여 이 대화에 전송해주세요."

            await update.message.reply_text(success_message)

            logger.info(f"Attendance records created: {len(created_records)} records for student={student.name}")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await update.message.reply_text(
                "죄송합니다. 메시지 처리 중 오류가 발생했습니다.\n"
                "잠시 후 다시 시도해주세요."
            )
        finally:
            db.close()

    def _register_parent_if_new(self, db: Session, student_id: int, telegram_user_id: str):
        """학부모 자동 등록 (이미 등록되어 있으면 스킵)"""
        try:
            # 이미 등록된 학부모인지 확인
            existing_parent = db.query(StudentParent).filter(
                StudentParent.student_id == student_id,
                StudentParent.telegram_id == telegram_user_id
            ).first()

            if not existing_parent:
                # 새 학부모 등록
                new_parent = StudentParent(
                    student_id=student_id,
                    telegram_id=telegram_user_id,
                    auto_registered=True,
                    is_active=True
                )
                db.add(new_parent)
                db.commit()
                logger.info(f"✅ 새 학부모 자동 등록: student_id={student_id}, telegram_id={telegram_user_id}")
            else:
                logger.info(f"✓ 이미 등록된 학부모: student_id={student_id}, telegram_id={telegram_user_id}")

        except Exception as e:
            logger.error(f"학부모 등록 중 오류: {e}")
            # 오류가 나도 출결 처리는 계속 진행

    async def _handle_cancel(self, db: Session, student: Student, message_text: str, update):
        """출결 기록 취소 처리"""
        # 가장 최근 출결 기록 찾기 (PENDING 상태만)
        recent_record = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.approval_status == ApprovalStatus.PENDING
        ).order_by(AttendanceRecord.created_at.desc()).first()

        if not recent_record:
            await update.message.reply_text(
                f"❌ {student.name} 학생의 승인 대기 중인 출결 기록이 없습니다.\n"
                f"이미 승인되거나 거부된 기록은 교사에게 문의해주세요."
            )
            return

        # 연관된 서류 제출 기록도 삭제
        from ..models import DocumentSubmission
        related_docs = db.query(DocumentSubmission).filter(
            DocumentSubmission.attendance_record_id == recent_record.id
        ).all()

        for doc in related_docs:
            db.delete(doc)

        # 출결 기록 삭제
        record_date = recent_record.date.strftime('%Y-%m-%d')
        record_type = recent_record.attendance_type.value
        db.delete(recent_record)
        db.commit()

        await update.message.reply_text(
            f"✅ 출결 기록이 취소되었습니다!\n\n"
            f"👤 학생: {student.name}\n"
            f"📅 날짜: {record_date}\n"
            f"📝 내용: {record_type}\n\n"
            f"취소된 기록은 복구할 수 없습니다."
        )
        logger.info(f"출결 기록 취소됨: student={student.name}, date={record_date}")

    async def _handle_update(self, db: Session, student: Student, extracted_data, message_text: str, update):
        """출결 기록 수정 처리"""
        # 가장 최근 출결 기록 찾기 (PENDING 상태만)
        recent_record = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.approval_status == ApprovalStatus.PENDING
        ).order_by(AttendanceRecord.created_at.desc()).first()

        if not recent_record:
            await update.message.reply_text(
                f"❌ {student.name} 학생의 승인 대기 중인 출결 기록이 없습니다.\n"
                f"먼저 출결 정보를 등록해주세요."
            )
            return

        # 출결 타입 매핑
        attendance_type_map = {
            "결석": AttendanceType.ABSENT,
            "조퇴": AttendanceType.EARLY_LEAVE,
            "지각": AttendanceType.LATE
        }

        # 출결 사유 매핑
        attendance_reason_map = {
            "질병": AttendanceReason.ILLNESS,
            "미인정": AttendanceReason.UNAUTHORIZED,
            "출석인정": AttendanceReason.AUTHORIZED
        }

        # 수정 사항 적용
        modified_fields = []
        if extracted_data.date:
            try:
                new_date = datetime.fromisoformat(extracted_data.date)
                recent_record.date = new_date
                modified_fields.append(f"날짜 → {extracted_data.date}")
            except:
                pass

        if extracted_data.attendance_type and extracted_data.attendance_type in attendance_type_map:
            recent_record.attendance_type = attendance_type_map[extracted_data.attendance_type]
            modified_fields.append(f"출결 타입 → {extracted_data.attendance_type}")

        if extracted_data.attendance_reason and extracted_data.attendance_reason in attendance_reason_map:
            recent_record.attendance_reason = attendance_reason_map[extracted_data.attendance_reason]
            modified_fields.append(f"출결 사유 → {extracted_data.attendance_reason}")

        if not modified_fields:
            await update.message.reply_text(
                "❌ 수정할 내용을 찾을 수 없습니다.\n"
                "예: '지각으로 수정', '내일로 변경', '질병으로 바꿔주세요'"
            )
            return

        # 수정 로그 저장
        recent_record.original_message = f"{recent_record.original_message}\n[수정: {message_text}]"
        db.commit()

        await update.message.reply_text(
            f"✅ 출결 기록이 수정되었습니다!\n\n"
            f"👤 학생: {student.name}\n"
            f"📝 수정 내용:\n" + "\n".join(f"  • {field}" for field in modified_fields) + "\n\n"
            f"교사 승인 대기 중입니다."
        )
        logger.info(f"출결 기록 수정됨: student={student.name}, modifications={modified_fields}")

    async def send_reminder(self, student_telegram_id: str, message: str):
        """독려 메시지 발송"""
        try:
            await self.application.bot.send_message(
                chat_id=student_telegram_id,
                text=message
            )
            logger.info(f"Reminder sent to {student_telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send reminder to {student_telegram_id}: {e}")
            return False

    def run(self):
        """봇 실행"""
        logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
