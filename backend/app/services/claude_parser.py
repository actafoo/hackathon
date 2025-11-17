import os
import json
from datetime import datetime, timedelta
from anthropic import Anthropic
from typing import Optional
from ..schemas import ExtractedAttendanceData


class ClaudeMessageParser:
    """Claude AI를 사용한 출결 메시지 파싱"""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        self.client = Anthropic(api_key=api_key)

    def parse_attendance_message(self, message: str) -> tuple[Optional[ExtractedAttendanceData], Optional[str]]:
        """
        텔레그램 메시지에서 출결 정보 추출

        Args:
            message: 텔레그램 메시지 원문

        Returns:
            (추출된 데이터, 에러 메시지)
        """

        # 현재 날짜 계산
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        today_str = today.strftime("%Y-%m-%d")
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")
        three_days_later = (tomorrow + timedelta(days=2)).strftime("%Y-%m-%d")

        # 요일 정보 (한글)
        weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        today_weekday = weekday_names[today.weekday()]

        # 다음주 금요일 계산 (금요일 = 4)
        # 먼저 이번주/다음 금요일을 찾고, 거기에 7일을 더함
        days_until_this_friday = (4 - today.weekday()) % 7
        if days_until_this_friday == 0:  # 오늘이 금요일
            days_until_this_friday = 7
        days_until_next_friday = days_until_this_friday + 7
        next_friday = (today + timedelta(days=days_until_next_friday)).strftime("%Y-%m-%d")

        prompt = f"""당신은 초등학교 출결 관리 담당자입니다. 학생이나 학부모가 보낸 메시지를 읽고 출결 정보와 요청 의도를 파악해주세요.

메시지: "{message}"

**맥락을 읽고 유연하게 추론해주세요:**

0. **사용자 의도 파악** (매우 중요! 신중하게 판단):
   - **create (출결 등록)**: 새로운 출결 정보를 알리는 경우
     * "홍길동 아파요", "김철수 늦습니다", "이영희 내일 체험학습"
     * "주선이 결석", "철수 지각", "영희 조퇴합니다"
   - **update (수정)**: 이전에 보낸 정보를 수정하려는 경우 (명시적으로 "수정", "바꿔", "변경" 등의 단어가 있어야 함)
     * "아까 잘못 보냈어요", "수정해주세요", "오늘이 아니라 내일이에요"
     * "지각이 아니라 결석이에요", "질병으로 바꿔주세요"
   - **cancel (취소)**: 이전에 보낸 정보를 취소하려는 경우 (출석 복귀, 괜찮아짐 등)
     * "취소해주세요", "잘못 보냈어요 삭제해주세요", "안 가기로 했어요"
     * "괜찮아졌어요", "등교합니다", "출석합니다", "가기로 했어요"
     * **주의**: "괜찮아졌어요"나 "등교합니다"는 cancel로 분류!

1. **학생 이름**:
   - "홍길동", "김철수" 같은 전체 이름
   - "길동", "길동이", "철수" 같은 이름만 (성 없이)
   - "~이" 형태도 인식 (예: "영희", "영희이" → "영희")
   - **update/cancel 시 학생 이름이 없으면 null 또는 빈 문자열("")로 설정**
   - **"에도", "또", "다시", "계속" 같은 단어가 있으면**:
     * 이전 기록 참조를 의미하므로 student_name은 null 또는 빈 문자열("")로 설정
     * 예: "다음주 금요일에도 못가요" → student_name: "", 신뢰도는 0.8 이상 (날짜와 상황은 명확)
   - create 시 이름이 없으면 보통 신뢰도를 낮춰야 하지만, "에도/또/다시" 같은 단어가 있으면 예외

2. **날짜 및 기간** (반드시 아래 정보를 정확히 사용하세요!):
   - **🔴 오늘**: {today_str} ({today_weekday})
   - **🔴 내일**: {tomorrow_str}
   - **🔴 다음주 금요일**: {next_friday} (절대 {next_friday}입니다!)

   - **날짜 변환 규칙**:
     * "오늘" → {today_str}
     * "내일" → {tomorrow_str}
     * "다음주 금요일" → {next_friday}
     * "11/20", "11월 20일" → 2025-11-20
     * 날짜가 없으면 → {today_str} (오늘)

   - **기간 인식**:
     * "내일부터 3일간" → date: {tomorrow_str}, end_date: {three_days_later}
     * "11/20부터 11/22까지" → date: 2025-11-20, end_date: 2025-11-22
     * 단일 날짜면 end_date는 null

3. **출결 타입** (결석/지각/조퇴 - 정확히 구분!):
   - 명시적으로 "결석", "지각", "조퇴"가 있으면 **반드시** 그대로 사용
   - 없으면 맥락으로 추론:
     * "못 갑니다", "갈 수 없습니다", "쉽니다", "안 갑니다", "아파요" → **결석**
     * "늦습니다", "늦을 것 같습니다", "늦게 갑니다", "늦어요" → **지각**
     * "조퇴합니다", "조퇴해요", "일찍 갑니다", "먼저 갑니다", "일찍 가야 합니다" → **조퇴**
   - **중요**: "조퇴합니다"는 반드시 "조퇴"로, "늦습니다"는 반드시 "지각"으로!

4. **출결 사유** (질병/미인정/출석인정 - 매우 신중하게 판단!):

   **🔴 사유가 명확한 경우만 설정하세요!**
   - **질병**: "아프다", "감기", "몸살", "병원", "열", "배탈", "두통", "약 먹는다", "아파서", "아파요" 등 **명시적** 표현
   - **출석인정**: "현장체험학습", "체험학습", "가족여행", "조부모 제사", "가족 행사" 등 **구체적** 사유
   - **미인정**: "늦잠", "개인 사정", "무단" 등 **명시적** 표현

   **⚠️ 다음 경우는 사유를 추측하지 말고 null로 설정하세요:**
   - "못가요", "갈 수 없어요", "안 가요" → 이유를 모름 → null
   - "결석", "지각", "조퇴" (단어만) → 이유를 모름 → null
   - "늦습니다", "늦어요" → 이유를 모름 → null
   - **사유가 명확하지 않으면 절대 "미인정"으로 추측하지 마세요!**

   **예시:**
   - "홍길동 결석" → attendance_reason: null, confidence: 0.5 (사유 없음)
   - "김철수 못가요" → attendance_reason: null, confidence: 0.6 (사유 없음)
   - "이영희 지각" → attendance_reason: null, confidence: 0.6 (사유 없음)
   - "홍길동 아파서 결석" → attendance_reason: "질병", confidence: 0.9 (사유 명확)

**응답 형식** (JSON만 반환):
{{
    "intent": "create" 또는 "update" 또는 "cancel",
    "student_name": "추출한 이름 (update/cancel 시 없으면 null 또는 빈 문자열)",
    "date": "YYYY-MM-DD (시작 날짜, update/cancel인 경우 생략 가능하면 오늘)",
    "end_date": "YYYY-MM-DD (종료 날짜, 기간인 경우만. 단일 날짜면 null)",
    "attendance_type": "결석" 또는 "지각" 또는 "조퇴" (update/cancel인 경우 null 가능),
    "attendance_reason": "질병" 또는 "미인정" 또는 "출석인정" (update/cancel인 경우 null 가능),
    "confidence": 0.0~1.0 (신뢰도)
}}

**신뢰도(confidence) 판단 기준 (매우 중요!):**
- **0.9-1.0**: 모든 정보가 명확하고 확실함 (예: "홍길동 아파서 오늘 결석합니다")
- **0.7-0.9**: 대부분 정보가 명확하지만 일부 추론이 필요함 (예: "길동이 아파요" - 성이 없음)
- **0.5-0.7**: 중요한 정보가 불명확하거나 추측이 많이 필요함
  * "아파요" - 학생 이름 없음 → 0.6
  * "홍길동 결석" - 사유 없음 → 0.5
  * "홍길동" - 상황과 사유 없음 → 0.3
- **0.3-0.5**: 대부분 정보를 추측해야 함
- **0.0-0.3**: 거의 확신할 수 없음

**🔴 중요**:
- 학생 이름, 출결 타입, **출결 사유** 중 하나라도 명확하지 않으면 신뢰도를 **0.6 이하**로 낮춰주세요!
- 사유가 없으면 절대 추측하지 말고 null + 낮은 신뢰도로 처리!

**⚠️ 경고: 아래 예시는 참고용입니다. 예시의 이름("홍길동", "철수" 등)을 실제 메시지에 사용하지 마세요! 메시지에서 직접 추출한 정보만 사용하세요.**

**예시:**

**create (출결 등록):**
- "홍길동 아파요" → intent: "create", student_name: "홍길동", date: "{today_str}", attendance_type: "결석", attendance_reason: "질병", confidence: 0.9
- "철수 늦습니다" → intent: "create", student_name: "철수", date: "{today_str}", attendance_type: "지각", attendance_reason: "미인정", confidence: 0.85
- "주선이 내일부터 3일간 체험학습갑니다" → intent: "create", student_name: "주선", date: "{tomorrow_str}", end_date: "{three_days_later}", attendance_type: "결석", attendance_reason: "출석인정", confidence: 0.9
- "다음주 금요일에도 못가요" → intent: "create", student_name: "", date: "{next_friday}", attendance_type: "결석", attendance_reason: "미인정", confidence: 0.8 (이름 없지만 "에도" 키워드로 참조)
- "또 아파요" → intent: "create", student_name: "", date: "{today_str}", attendance_type: "결석", attendance_reason: "질병", confidence: 0.8 (이름 없지만 "또" 키워드로 참조)
- "내일도 못가요" → intent: "create", student_name: "", date: "{tomorrow_str}", attendance_type: "결석", attendance_reason: "미인정", confidence: 0.8 (이름 없지만 "도" 키워드로 참조)

**update (수정):**
- "아까 잘못 보냈어요. 영희 결석이 아니라 지각이에요" → intent: "update", student_name: "영희", attendance_type: "지각"
- "수정해주세요. 홍길동 내일이 아니라 오늘이에요" → intent: "update", student_name: "홍길동", date: "{today_str}"
- "철수 질병으로 바꿔주세요" → intent: "update", student_name: "철수", attendance_reason: "질병"
- "지각으로 바꿔주세요" → intent: "update", student_name: "", attendance_type: "지각"

**cancel (취소):**
- "김민수 취소해주세요" → intent: "cancel", student_name: "김민수"
- "아까 보낸 거 잘못 보냈어요. 영희 등교합니다" → intent: "cancel", student_name: "영희"
- "괜찮아졌어요. 홍길동 취소" → intent: "cancel", student_name: "홍길동"

**중요**: 완벽하지 않아도 괜찮습니다. 맥락을 읽고 최선을 다해 추론해주세요!
"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # 응답에서 JSON 추출
            response_text = response.content[0].text.strip()

            # 디버깅: 응답 로그 출력
            print(f"[DEBUG] Claude AI 원본 응답: {response_text}")

            # JSON 블록에서 추출 (```json ... ``` 형태일 경우)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            else:
                # JSON 블록이 없는 경우, 중괄호로 JSON 찾기
                if "{" in response_text and "}" in response_text:
                    json_start = response_text.find("{")
                    # 마지막 중괄호를 찾기 위해 역순으로 탐색
                    json_end = response_text.rfind("}") + 1
                    response_text = response_text[json_start:json_end].strip()

            # 디버깅: 추출된 JSON 로그 출력
            print(f"[DEBUG] 추출된 JSON: {response_text}")

            # JSON이 비어있으면 에러 반환
            if not response_text:
                return None, "Claude AI 응답이 비어있습니다."

            # JSON 파싱
            data = json.loads(response_text)

            # 신뢰도 체크 (엄격하게)
            confidence = data.get("confidence", 0)

            # "에도", "또", "다시" 같은 키워드가 있으면 이전 기록 참조이므로 이름 없어도 OK
            reference_keywords = ["에도", "또", "다시", "계속"]
            has_reference_keyword = any(keyword in message for keyword in reference_keywords)

            if confidence < 0.7:
                # 신뢰도가 낮은 경우 구체적인 안내 제공
                missing_info = []
                if not data.get("student_name") and not has_reference_keyword:
                    missing_info.append("학생 이름")
                if not data.get("attendance_type"):
                    missing_info.append("출결 상황 (결석/지각/조퇴)")
                if not data.get("attendance_reason"):
                    missing_info.append("사유 (아파서/체험학습/개인사정 등)")

                if missing_info:
                    return None, f"다음 정보가 명확하지 않습니다: {', '.join(missing_info)}\n\n좀 더 명확하게 알려주세요.\n예: '홍길동 아파서 결석', '김철수 늦잠 자서 지각', '이영희 체험학습'"
                else:
                    return None, "메시지 내용이 명확하지 않습니다.\n\n학생 이름과 상황을 자세히 알려주세요.\n예: '홍길동 아파요', '김철수 늦습니다'"

            # 데이터 검증
            extracted_data = ExtractedAttendanceData(**data)

            # 의도 검증
            valid_intents = ["create", "update", "cancel"]
            if extracted_data.intent not in valid_intents:
                return None, f"올바르지 않은 의도입니다: {extracted_data.intent}"

            # 출결 타입과 사유 검증 (create인 경우 필수)
            if extracted_data.intent == "create":
                valid_types = ["결석", "조퇴", "지각"]
                valid_reasons = ["질병", "미인정", "출석인정"]

                if not extracted_data.attendance_type or extracted_data.attendance_type not in valid_types:
                    return None, f"출결 등록 시 올바른 출결 타입이 필요합니다"

                if not extracted_data.attendance_reason or extracted_data.attendance_reason not in valid_reasons:
                    return None, f"출결 등록 시 올바른 출결 사유가 필요합니다"

            # update/cancel인 경우 타입과 사유는 선택사항이므로 검증 스킵

            return extracted_data, None

        except json.JSONDecodeError as e:
            return None, f"응답 파싱 오류: {str(e)}"
        except Exception as e:
            return None, f"메시지 분석 중 오류 발생: {str(e)}"

    def generate_clarification_message(self, original_message: str, error: str) -> str:
        """
        추출 실패 시 사용자에게 보낸 안내 메시지 생성

        Args:
            original_message: 원본 메시지
            error: 에러 메시지

        Returns:
            사용자에게 보낼 안내 메시지
        """
        return f"""죄송합니다. 메시지를 이해하지 못했습니다.

다음과 같이 간단히 알려주세요:

📝 예시:
• "홍길동 아파요"
• "김철수 늦습니다"
• "이영희 현장체험학습"
• "박민수 오늘 못 갑니다"

💡 학생 이름과 상황만 알려주시면 됩니다!
"""
