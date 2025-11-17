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

        # 요일 정보 (한글)
        weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        today_weekday = weekday_names[today.weekday()]

        prompt = f"""당신은 초등학교 출결 관리 시스템입니다. 학부모/학생이 보낸 메시지를 읽고 출결 정보를 파악해주세요.

**오늘 날짜**: {today_str} ({today_weekday})
**내일 날짜**: {tomorrow_str}

**메시지**: "{message}"

---

## 출결 분류 체계

출결은 **타입 × 사유 = 9가지 조합**으로 구성됩니다:

### 출결 타입 (3가지)
1. **결석**: 하루 종일 학교에 오지 않음
2. **지각**: 늦게 등교함
3. **조퇴**: 수업 중간에 일찍 하교함

### 출결 사유 (3가지)
1. **질병**: 아픔, 병원 방문, 감기, 몸살, 열, 배탈 등 건강 문제
2. **출석인정**: 현장체험학습, 체험학습, 가족여행, 법정감염병, 조부모 제사 등 공식적으로 인정되는 사유
3. **미인정**: 개인 사정, 늦잠, 무단 등 기타 사유

### 9가지 조합
- 질병결석, 질병지각, 질병조퇴
- 출석인정결석, 출석인정지각, 출석인정조퇴
- 미인정결석, 미인정지각, 미인정조퇴

---

## 사용자 의도 파악

1. **create (새 출결 등록)**: 새로운 출결 정보를 알리는 경우
   - 예: "홍길동 아파요", "내일 조퇴합니다", "3교시 끝나고 가야 해요"

2. **update (수정)**: 이전 출결 정보를 수정 (명시적으로 "수정", "바꿔", "변경" 등의 단어 필요)
   - 예: "아까 잘못 보냈어요", "지각이 아니라 결석이에요"

3. **cancel (취소)**: 이전 출결 정보를 취소
   - 예: "취소해주세요", "괜찮아졌어요", "등교합니다"

---

## 추출 가이드

**메시지를 자연스럽게 읽고 맥락을 파악하세요:**

1. **학생 이름**: 메시지에서 언급된 이름 추출
   - "홍길동", "길동이", "주선" 등
   - 이름이 없으면 빈 문자열("") 또는 null

2. **날짜**:
   - "오늘" → {today_str}
   - "내일" → {tomorrow_str}
   - "11/20", "11월 20일" → 2025-11-20
   - 날짜 언급 없으면 → {today_str}
   - 기간("내일부터 3일간") → date와 end_date 모두 설정

3. **출결 타입 자연스럽게 판단**:
   - 하루 종일 학교에 안 오는 상황 → **결석**
   - 늦게 오는 상황 → **지각**
   - 중간에 일찍 가는 상황 → **조퇴**
   - **"3교시 끝나고", "점심시간에", "오후에 가야", "수업 끝나고" → 조퇴**

4. **출결 사유 신중하게 판단**:
   - **명확한 질병 표현**("아파요", "병원", "감기", "열") → 질병
   - **명확한 공식 사유**("체험학습", "현장체험학습", "법정감염병") → 출석인정
   - **명확한 개인 사유**("늦잠", "개인 사정") → 미인정
   - **사유 불명확하면 null로 설정하고 추가 질문 요청**

5. **신뢰도(confidence)**:
   - 모든 정보가 명확 → 0.9-1.0
   - 일부 정보 추론 필요 → 0.7-0.9
   - 중요 정보 불명확 → 0.5-0.7
   - **사유가 불명확하면 반드시 0.6 이하**

---

## 응답 형식 (JSON)

{{
    "intent": "create" | "update" | "cancel",
    "student_name": "학생 이름 또는 빈 문자열",
    "date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD 또는 null",
    "attendance_type": "결석" | "지각" | "조퇴" | null,
    "attendance_reason": "질병" | "출석인정" | "미인정" | null,
    "confidence": 0.0~1.0,
    "clarification_needed": true | false,
    "clarification_question": "추가 질문 (필요시)"
}}

---

## 중요 원칙

1. **맥락을 자연스럽게 읽고 이해하세요**
2. **불확실하면 추측하지 말고 추가 질문하세요**
3. **사유가 명확하지 않으면 반드시 clarification_needed: true**
4. **예시의 이름을 사용하지 말고 메시지에서 직접 추출하세요**

---

## 예시

**입력**: "주선이 내일 3교시 끝나고 조퇴할게요"
**출력**:
{{
    "intent": "create",
    "student_name": "주선",
    "date": "{tomorrow_str}",
    "end_date": null,
    "attendance_type": "조퇴",
    "attendance_reason": null,
    "confidence": 0.6,
    "clarification_needed": true,
    "clarification_question": "조퇴 사유를 알려주시겠어요? (예: 아파서, 병원 가야 해서, 개인 사정)"
}}

**입력**: "홍길동 아파서 결석입니다"
**출력**:
{{
    "intent": "create",
    "student_name": "홍길동",
    "date": "{today_str}",
    "end_date": null,
    "attendance_type": "결석",
    "attendance_reason": "질병",
    "confidence": 0.95,
    "clarification_needed": false,
    "clarification_question": null
}}

**입력**: "김철수 체험학습으로 내일부터 3일간 결석"
**출력**:
{{
    "intent": "create",
    "student_name": "김철수",
    "date": "{tomorrow_str}",
    "end_date": "{(tomorrow + timedelta(days=2)).strftime('%Y-%m-%d')}",
    "attendance_type": "결석",
    "attendance_reason": "출석인정",
    "confidence": 0.95,
    "clarification_needed": false,
    "clarification_question": null
}}

이제 위 메시지를 분석하여 JSON만 반환하세요. 다른 설명은 필요 없습니다.
"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Haiku (개선된 프롬프트 사용)
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

            # JSON 블록에서 추출
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
                    json_end = response_text.rfind("}") + 1
                    response_text = response_text[json_start:json_end].strip()

            print(f"[DEBUG] 추출된 JSON: {response_text}")

            if not response_text:
                return None, "AI 응답을 파싱할 수 없습니다."

            # JSON 파싱
            data = json.loads(response_text)

            # 추가 질문이 필요한 경우
            if data.get("clarification_needed"):
                clarification_msg = data.get("clarification_question", "다음 정보를 추가로 알려주세요:")
                return None, clarification_msg

            # 신뢰도 체크
            confidence = data.get("confidence", 0)
            if confidence < 0.6:
                return None, "메시지 내용이 명확하지 않습니다.\n\n학생 이름, 날짜, 출결 상황, 사유를 자세히 알려주세요.\n\n예: '홍길동 아파서 내일 결석', '김철수 체험학습으로 3일간 결석'"

            # 데이터 검증
            extracted_data = ExtractedAttendanceData(**data)

            # create인 경우 필수 필드 검증
            if extracted_data.intent == "create":
                if not extracted_data.attendance_type:
                    return None, "출결 타입(결석/지각/조퇴)을 명확히 알려주세요."
                if not extracted_data.attendance_reason:
                    return None, f"출결 사유를 알려주세요.\n\n예:\n• 아파서 → 질병\n• 체험학습 → 출석인정\n• 개인 사정 → 미인정"

            return extracted_data, None

        except json.JSONDecodeError as e:
            return None, f"응답 파싱 오류: {str(e)}"
        except Exception as e:
            return None, f"메시지 분석 중 오류 발생: {str(e)}"

    def generate_clarification_message(self, original_message: str, error: str) -> str:
        """
        추출 실패 시 사용자에게 보낼 안내 메시지 생성

        Args:
            original_message: 원본 메시지
            error: 에러 메시지

        Returns:
            사용자에게 보낼 안내 메시지
        """
        return f"""{error}

📝 다시 보내주실 때는 다음 정보를 포함해주세요:
• 학생 이름
• 날짜 (오늘/내일 등)
• 상황 (결석/지각/조퇴)
• 사유 (아파서/체험학습/개인 사정 등)

예시:
• "홍길동 아파서 내일 결석"
• "김철수 늦잠 자서 오늘 지각"
• "이영희 체험학습으로 내일부터 3일간 결석"
"""
