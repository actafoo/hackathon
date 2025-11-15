import os
import json
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
   - create 시에는 학생 이름이 반드시 필요

2. **날짜 및 기간**:
   - "오늘", "내일", "어제" 등의 표현을 오늘 기준 날짜로 변환해주세요 (오늘: 2025-11-15)
   - 날짜가 없으면 오늘로 가정합니다
   - "11/20", "11월 20일" 등은 2025-11-20으로 변환
   - **기간 인식**:
     * "내일부터 3일간" → date: 2025-11-16, end_date: 2025-11-18 (3일간)
     * "금요일까지" → date: 오늘, end_date: 다음 금요일
     * "11/20부터 11/22까지" → date: 2025-11-20, end_date: 2025-11-22
     * "월요일부터 수요일까지" → date: 다음 월요일, end_date: 다음 수요일
   - 기간이 아닌 단일 날짜면 end_date는 null로 설정

3. **출결 타입** (결석/지각/조퇴 - 정확히 구분!):
   - 명시적으로 "결석", "지각", "조퇴"가 있으면 **반드시** 그대로 사용
   - 없으면 맥락으로 추론:
     * "못 갑니다", "갈 수 없습니다", "쉽니다", "안 갑니다", "아파요" → **결석**
     * "늦습니다", "늦을 것 같습니다", "늦게 갑니다", "늦어요" → **지각**
     * "조퇴합니다", "조퇴해요", "일찍 갑니다", "먼저 갑니다", "일찍 가야 합니다" → **조퇴**
   - **중요**: "조퇴합니다"는 반드시 "조퇴"로, "늦습니다"는 반드시 "지각"으로!

4. **출결 사유** (질병/미인정/출석인정 - 신중하게 판단!):
   - **질병**: 아프다, 감기, 몸살, 병원, 열, 배탈, 두통, 약 먹는다, 아파서, 아파요 등
   - **출석인정**: 현장체험학습, 체험학습, 가족여행, 조부모 제사, 가족 행사, 공적 행사, 학교 허가받은 사유
   - **미인정**: 늦잠, 개인 사정, 무단, 사유 미상, 그냥, 기타 개인 사유
   - **기본값**: 사유가 명시되지 않으면 **"미인정"**으로 설정
   - **주의**: "결석" 단어만 있고 사유가 없으면 → 미인정

**응답 형식** (JSON만 반환):
{{
    "intent": "create" 또는 "update" 또는 "cancel",
    "student_name": "추출한 이름 (update/cancel 시 없으면 null 또는 빈 문자열)",
    "date": "YYYY-MM-DD (시작 날짜, update/cancel인 경우 생략 가능하면 오늘)",
    "end_date": "YYYY-MM-DD (종료 날짜, 기간인 경우만. 단일 날짜면 null)",
    "attendance_type": "결석" 또는 "지각" 또는 "조퇴" (update/cancel인 경우 null 가능),
    "attendance_reason": "질병" 또는 "미인정" 또는 "출석인정" (update/cancel인 경우 null 가능),
    "confidence": 0.0~1.0
}}

**예시:**

**create (출결 등록):**
- "홍길동 아파요" → intent: "create", student_name: "홍길동", date: "2025-11-15", attendance_type: "결석", attendance_reason: "질병"
- "철수 늦습니다" → intent: "create", student_name: "철수", date: "2025-11-15", attendance_type: "지각", attendance_reason: "미인정"
- "주선이 내일부터 3일간 체험학습갑니다" → intent: "create", student_name: "주선", date: "2025-11-16", end_date: "2025-11-18", attendance_type: "결석", attendance_reason: "출석인정"

**update (수정):**
- "아까 잘못 보냈어요. 영희 결석이 아니라 지각이에요" → intent: "update", student_name: "영희", attendance_type: "지각"
- "수정해주세요. 홍길동 내일이 아니라 오늘이에요" → intent: "update", student_name: "홍길동", date: "2025-11-15"
- "철수 질병으로 바꿔주세요" → intent: "update", student_name: "철수", attendance_reason: "질병"
- "13일로 수정해주세요" → intent: "update", student_name: "", date: "2025-11-13"
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

            # 신뢰도 체크 (더 유연하게)
            if data.get("confidence", 0) < 0.3:
                return None, "메시지에서 출결 정보를 찾을 수 없습니다. 학생 이름과 상황을 알려주세요."

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
