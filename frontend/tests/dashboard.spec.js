import { test, expect } from '@playwright/test'

// API mock: 백엔드 없이 프론트엔드만 테스트
test.beforeEach(async ({ page }) => {
  // 월별 그리드 API mock
  await page.route('**/api/attendance/monthly-grid**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        students: [
          { id: 1, name: '김철수', student_number: 1, telegram_id: null },
          { id: 2, name: '이영희', student_number: 2, telegram_id: 'test123' },
          { id: 3, name: '박민준', student_number: 3, telegram_id: null },
        ],
        attendance_data: [
          {
            id: 1,
            student_id: 1,
            date: '2026-06-03',
            attendance_type: '결석',
            attendance_reason: '질병',
            approval_status: '대기',
            document_submitted: false,
            notes: '병원 진료',
          },
          {
            id: 2,
            student_id: 2,
            date: '2026-06-05',
            attendance_type: '지각',
            attendance_reason: '미인정',
            approval_status: '승인',
            document_submitted: false,
            notes: '',
          },
          {
            id: 3,
            student_id: 1,
            date: '2026-06-10',
            attendance_type: '조퇴',
            attendance_reason: '출석인정',
            approval_status: '거부',
            document_submitted: true,
            notes: '현장체험학습',
          },
        ],
        year: 2026,
        month: 6,
      }),
    })
  })

  // 독려 메시지 API mock
  await page.route('**/api/attendance/send-reminders', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ sent_count: 2, failed_count: 0 }),
    })
  })
})

test.describe('대시보드 기본 렌더링', () => {
  test('헤더가 올바르게 표시된다', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('출결 관리 시스템')
    await expect(page.locator('.header-subtitle')).toContainText('대시보드')
  })

  test('연도/월 선택 셀렉트박스가 표시된다', async ({ page }) => {
    await page.goto('/')
    const yearSelect = page.locator('select').first()
    const monthSelect = page.locator('select').nth(1)
    await expect(yearSelect).toBeVisible()
    await expect(monthSelect).toBeVisible()
  })

  test('통계 카드 5개가 표시된다', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.stat-card')).toHaveCount(5)
  })

  test('통계 카드 값이 정확하게 표시된다', async ({ page }) => {
    await page.goto('/')
    const statValues = page.locator('.stat-value')
    await expect(statValues.nth(0)).toHaveText('3') // 전체 학생
    await expect(statValues.nth(1)).toHaveText('3') // 이번 달 출결
    await expect(statValues.nth(2)).toHaveText('1') // 승인 대기
    await expect(statValues.nth(3)).toHaveText('1') // 승인 완료
  })
})

test.describe('출결 그리드', () => {
  test('학생 목록이 그리드에 표시된다', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('김철수')).toBeVisible()
    await expect(page.getByText('이영희')).toBeVisible()
    await expect(page.getByText('박민준')).toBeVisible()
  })

  test('출결 기호가 올바르게 표시된다', async ({ page }) => {
    await page.goto('/')
    // 결석-질병 → ♡ (그리드 셀 내부의 symbol-large)
    await expect(page.locator('.symbol-large').getByText('♡')).toBeVisible()
    // 지각-미인정 → ×
    await expect(page.locator('.symbol-large').getByText('×')).toBeVisible()
    // 조퇴-출석인정 → ▷
    await expect(page.locator('.symbol-large').getByText('▷')).toBeVisible()
  })

  test('출결 셀 클릭 시 모달이 열린다', async ({ page }) => {
    await page.goto('/')
    // 출결 기록이 있는 셀 클릭 (symbol-large 내부 ♡)
    await page.locator('.symbol-large').getByText('♡').click()
    await expect(page.locator('.modal-content')).toBeVisible({ timeout: 3000 })
  })
})

test.describe('월 변경', () => {
  test('월을 변경하면 데이터가 다시 로드된다', async ({ page }) => {
    await page.goto('/')
    const monthSelect = page.locator('select').nth(1)
    await monthSelect.selectOption('7')
    await expect(monthSelect).toHaveValue('7')
  })

  test('조회 버튼이 동작한다', async ({ page }) => {
    await page.goto('/')
    const queryBtn = page.locator('.btn-query')
    await expect(queryBtn).toBeVisible()
    await queryBtn.click()
    // 로딩 후 그리드 다시 표시
    await expect(page.locator('.stat-card')).toHaveCount(5)
  })
})

test.describe('액션 버튼', () => {
  test('학생 관리 버튼이 표시된다', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('학생 관리')).toBeVisible()
  })

  test('새로고침 버튼이 동작한다', async ({ page }) => {
    await page.goto('/')
    await page.getByText('새로고침').click()
    await expect(page.locator('.stat-card')).toHaveCount(5)
  })

  test('학생 관리 클릭 시 모달이 열린다', async ({ page }) => {
    // 학생 목록 API mock 추가
    await page.route('**/api/students**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, name: '김철수', student_number: 1, telegram_id: null },
          { id: 2, name: '이영희', student_number: 2, telegram_id: 'test123' },
        ]),
      })
    })
    await page.goto('/')
    await page.getByText('학생 관리').click()
    await expect(page.locator('.modal-content.modal-large')).toBeVisible({ timeout: 3000 })
  })
})
