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

    def parse_attendance_message(self, message: str, context: dict = None) -> tuple[Optional[ExtractedAttendanceData], Optional[str]]:
        """
        텔레그램 메시지에서 출결 정보 추출

        Args:
            message: 텔레그램 메시지 원문
            context: 이전 대화 맥락 (선택)
                {
                    'messages': [{'text': '...', 'timestamp': ...}],
                    'partial_data': {'student_name': '...', ...}
                }

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

        # 다음주 날짜 계산 (월~일)
        days_until_next_monday = (7 - today.weekday()) % 7 or 7
        next_week_monday = today + timedelta(days=days_until_next_monday)
        next_week_dates = {
            "월요일": (next_week_monday).strftime("%Y-%m-%d"),
            "화요일": (next_week_monday + timedelta(days=1)).strftime("%Y-%m-%d"),
            "수요일": (next_week_monday + timedelta(days=2)).strftime("%Y-%m-%d"),
            "목요일": (next_week_monday + timedelta(days=3)).strftime("%Y-%m-%d"),
            "금요일": (next_week_monday + timedelta(days=4)).strftime("%Y-%m-%d"),
            "토요일": (next_week_monday + timedelta(days=5)).strftime("%Y-%m-%d"),
            "일요일": (next_week_monday + timedelta(days=6)).strftime("%Y-%m-%d"),
        }

        # 대화 맥락 처리
        context_info = ""
        has_context = False
        partial_data = context.get('partial_data', {}) if context else {}

        if context and context.get('messages'):
            has_context = True
            context_info = "\n\n## 🔄 대화 맥락이 있습니다 - 이전 정보와 현재 메시지를 합쳐주세요!\n\n"
            context_info += "**이전 대화 내용:**\n"
            for msg in context['messages'][-3:]:  # 최근 3개 메시지만
                context_info += f"- {msg['text']}\n"
            context_info += f"\n**현재 메시지**: {message}\n"

        if partial_data:
            has_context = True
            context_info += f"\n**이미 알고 있는 정보 (반드시 유지하세요!):**\n"
            context_info += f"```json\n{json.dumps(partial_data, ensure_ascii=False, indent=2)}\n```\n"
            context_info += "\n**⚠️ 매우 중요:**\n"
            context_info += "1. 위의 '이미 알고 있는 정보'에서 null이 아닌 값들은 **반드시 그대로 유지**하세요\n"
            context_info += "2. 현재 메시지에서 **새로운 정보(사유, 날짜 등)를 추출**하여 null 필드만 채우세요\n"
            context_info += "3. 현재 메시지가 짧더라도, 이전 정보와 결합하면 완전한 데이터가 됩니다\n"
            context_info += "4. 이전 정보의 student_name, date, attendance_type 등을 **절대 null로 만들지 마세요**\n\n"

        prompt = f"""당신은 초등학교 출결 관리 시스템입니다. 학부모/학생이 보낸 메시지를 읽고 출결 정보를 파악해주세요.

**메시지**: "{message}"

---

## 🚨 STEP 1: 먼저 출결 메시지인지 확인! (제일 중요!)

다음 메시지는 **출결 메시지가 아닙니다**. 이런 경우 intent: null로 설정하세요:
- ❌ "오늘은 몇일이죠?", "오늘 날짜 알려주세요" → 날짜 질문
- ❌ "안녕하세요", "감사합니다", "고맙습니다" → 인사/감사
- ❌ "네", "알겠습니다", "확인했어요" → 단순 응답
- ❌ "사용법 알려주세요", "어떻게 보내나요?" → 도움말 요청

**출결 메시지 특징 (이런 게 있어야 출결 메시지임!):**
- ✅ 학생 이름 + 출결 상황 (예: "홍길동 아파요", "주선이 결석")
- ✅ 출결 타입 명시 (예: "지각합니다", "조퇴할게요", "결석합니다")
- ✅ 출결 사유 설명 (예: "병원 가야 해서", "아파서", "체험학습")

**현재 메시지가 위 특징이 없다면 → intent: null**

---{context_info}

**오늘 날짜**: {today_str} ({today_weekday})
**내일 날짜**: {tomorrow_str}

**다음주 날짜:**
- 다음주 월요일: {next_week_dates['월요일']}
- 다음주 화요일: {next_week_dates['화요일']}
- 다음주 수요일: {next_week_dates['수요일']}
- 다음주 목요일: {next_week_dates['목요일']}
- 다음주 금요일: {next_week_dates['금요일']}
- 다음주 토요일: {next_week_dates['토요일']}
- 다음주 일요일: {next_week_dates['일요일']}

---

## 출결 분류 체계 (⚠️ 매우 중요!)

출결은 **두 개의 독립적인 필드**로 구성됩니다:
- **attendance_type** (타입): 무엇을 하는가? (결석/지각/조퇴)
- **attendance_reason** (사유): 왜 그러는가? (질병/출석인정/미인정)

⚠️ **절대로 헷갈리지 마세요:**
- "아파요" → attendance_type: "결석", attendance_reason: "질병"
- "질병"은 타입이 아니라 **사유**입니다!
- attendance_type은 **반드시** "결석", "지각", "조퇴" 중 하나여야 합니다!

### 출결 타입 (attendance_type) - 3가지만 가능
1. **결석**: 하루 종일 학교에 오지 않음
2. **지각**: 늦게 등교함
3. **조퇴**: 수업 중간에 일찍 하교함

⚠️ **주의**: attendance_type은 "질병", "출석인정", "미인정"이 절대 될 수 없습니다!

### 출결 사유 (attendance_reason) - 3가지만 가능
1. **질병**: 아픔, 병원 방문, 감기, 몸살, 열, 배탈 등 건강 문제
2. **출석인정**: 현장체험학습, 체험학습, 가족여행, 법정감염병, 조부모 제사 등 공식적으로 인정되는 사유
3. **미인정**: 개인 사정, 늦잠, 무단 등 기타 사유

### 예시: 9가지 조합 (타입 × 사유)
- "아파서 결석" → 타입:결석 + 사유:질병 = 질병결석
- "아파서 지각" → 타입:지각 + 사유:질병 = 질병지각
- "아파서 조퇴" → 타입:조퇴 + 사유:질병 = 질병조퇴
- "체험학습으로 결석" → 타입:결석 + 사유:출석인정 = 출석인정결석
- "늦잠 자서 지각" → 타입:지각 + 사유:미인정 = 미인정지각

---

## 사용자 의도 파악

⚠️ **먼저 출결 메시지인지 확인하세요!** 출결과 무관한 질문/인사는 intent: null로 설정!

1. **null (출결 메시지 아님)**: 단순 질문, 인사, 응답 등
   - 예: "오늘 몇일이죠?", "안녕하세요", "감사합니다"
   - **처리**: intent: null, clarification_question: "적절한 응답"

2. **create (새 출결 등록)**: 새로운 출결 정보를 알리는 경우
   - 예: "홍길동 아파요", "내일 조퇴합니다", "3교시 끝나고 가야 해요"

3. **update (수정)**: 이전 출결 정보를 수정 (명시적으로 "수정", "바꿔", "변경" 등의 단어 필요)
   - 예: "아까 잘못 보냈어요", "지각이 아니라 결석이에요"

4. **cancel (취소)**: 이전 출결 정보를 취소
   - 예: "취소해주세요", "괜찮아졌어요", "등교합니다"

---

## 추출 가이드

**메시지를 자연스럽게 읽고 맥락을 파악하세요:**

1. **학생 이름**: 메시지에서 언급된 이름 추출
   - "홍길동", "길동이", "주선" 등
   - 이름이 없으면 빈 문자열("") 또는 null

2. **날짜** (⚠️ 정확히 계산하세요!):
   - "오늘" → {today_str}
   - "내일" → {tomorrow_str}
   - **"다음주 월요일"** → {next_week_dates['월요일']}
   - **"다음주 화요일"** → {next_week_dates['화요일']}
   - **"다음주 수요일"** → {next_week_dates['수요일']}
   - **"다음주 목요일"** → {next_week_dates['목요일']}
   - **"다음주 금요일"** → {next_week_dates['금요일']}
   - **"다음주 토요일"** → {next_week_dates['토요일']}
   - **"다음주 일요일"** → {next_week_dates['일요일']}
   - "11/20", "11월 20일" → 2025-11-20
   - 날짜 언급 없으면 → {today_str}
   - 기간("내일부터 3일간") → date와 end_date 모두 설정

3. **출결 타입 정확하게 판단 (매우 중요!):**

   **결석** (학교에 안 옴, 하루 종일 없음):
   - "결석", "못 가요", "안 가요", "쉬어요", "학교 안 가요"
   - 예: "홍길동 오늘 결석", "아파서 못 가요"

   **지각** (늦게 등교함, 늦게 도착):
   - **"지각", "늦습니다", "늦게 가요", "늦게 와요", "늦어요"**
   - ⚠️ 핵심: 등교는 하지만 **늦게 도착**하는 것
   - 예: "주선이 지각해요", "늦게 갈게요", "10시에 등교합니다"

   **조퇴** (일찍 하교함, 수업 중 떠남):
   - "조퇴", "일찍 가요", "먼저 가요", "빼주세요"
   - "3교시 끝나고", "점심시간에", "오후에", "수업 끝나고"
   - ⚠️ 핵심: 등교는 했지만 **수업 중에 일찍 집에 감**
   - 예: "3교시 끝나고 조퇴", "점심 먹고 가야 해요"

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

1. **대화 맥락이 있으면 반드시 이전 정보를 유지하세요 (null이 아닌 값들은 절대 지우지 말 것!)**
2. **맥락을 자연스럽게 읽고 이해하세요**
3. **불확실하면 추측하지 말고 추가 질문하세요**
4. **사유가 명확하지 않으면 반드시 clarification_needed: true**
5. **예시의 이름을 사용하지 말고 메시지에서 직접 추출하세요**

---

## 예시

### 예시 1: 대화 맥락 - 이전 정보 유지 (매우 중요!)

**이미 알고 있는 정보**:
```json
{{
  "student_name": "주선",
  "date": "2025-11-18",
  "attendance_type": "지각",
  "attendance_reason": null
}}
```

**현재 메시지**: "병원 가야 해서요"

**출력** (이전 정보 유지 + 새 정보 추가):
{{
    "intent": "create",
    "student_name": "주선",
    "date": "2025-11-18",
    "end_date": null,
    "attendance_type": "지각",
    "attendance_reason": "질병",
    "confidence": 0.95,
    "clarification_needed": false,
    "clarification_question": null
}}

### 예시 2: 출결 메시지가 아닌 경우 (⚠️ 중요!)

**입력**: "오늘은 몇일이죠?"
**출력**:
{{
    "intent": null,
    "student_name": "",
    "date": null,
    "end_date": null,
    "attendance_type": null,
    "attendance_reason": null,
    "confidence": 1.0,
    "clarification_needed": true,
    "clarification_question": "오늘은 {today_str} ({today_weekday})입니다.\\n\\n출결 정보를 보내려면 다음과 같이 보내주세요:\\n예: '홍길동 아파서 결석', '내일 지각합니다'"
}}

### 예시 3: 다음주 날짜 계산

**입력**: "주선이 다음주 수요일에 지각해요"
**출력**:
{{
    "intent": "create",
    "student_name": "주선",
    "date": "{next_week_dates['수요일']}",
    "end_date": null,
    "attendance_type": "지각",
    "attendance_reason": null,
    "confidence": 0.6,
    "clarification_needed": true,
    "clarification_question": "지각 사유를 알려주시겠어요? (예: 아파서, 병원 가야 해서, 개인 사정)"
}}

### 예시 4: 조퇴

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

### 예시 3: 지각 (늦게 등교)

**입력**: "주선이 다음주 화요일에 지각해요"
**출력**:
{{
    "intent": "create",
    "student_name": "주선",
    "date": "2025-11-18",
    "end_date": null,
    "attendance_type": "지각",
    "attendance_reason": null,
    "confidence": 0.6,
    "clarification_needed": true,
    "clarification_question": "지각 사유를 알려주시겠어요? (예: 아파서, 병원 가야 해서, 개인 사정)"
}}

### 예시 4: 결석 (주의: 타입 vs 사유 구분!)

**입력**: "주선이 오늘 아파요"
**출력**:
{{
    "intent": "create",
    "student_name": "주선",
    "date": "{today_str}",
    "end_date": null,
    "attendance_type": "결석",
    "attendance_reason": "질병",
    "confidence": 0.9,
    "clarification_needed": false,
    "clarification_question": null
}}
⚠️ **주의**: "아파요"는 결석의 **사유(질병)**이지 **타입**이 아닙니다!

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

### 예시 5: 체험학습

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
