import React, { useState, useMemo } from 'react'
import AttendanceModal from './AttendanceModal'
import dayjs from 'dayjs'

const AttendanceGrid = ({ year, month, students, attendanceData, onUpdate }) => {
  const [selectedCell, setSelectedCell] = useState(null)

  // 해당 월의 일수 계산
  const daysInMonth = dayjs(`${year}-${month}-01`).daysInMonth()
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1)

  // 출결 데이터를 학생ID + 날짜로 빠르게 조회할 수 있도록 맵 생성
  const attendanceMap = useMemo(() => {
    const map = new Map()
    attendanceData.forEach(record => {
      const date = dayjs(record.date).date()
      const key = `${record.student_id}-${date}`
      map.set(key, record)
    })
    return map
  }, [attendanceData])

  // 셀 클릭 핸들러
  const handleCellClick = (student, day) => {
    const key = `${student.id}-${day}`
    const record = attendanceMap.get(key)
    setSelectedCell({
      student,
      day,
      date: `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
      record
    })
  }

  // 모달 닫기
  const handleCloseModal = () => {
    setSelectedCell(null)
    onUpdate()
  }

  // 9가지 조합을 하나의 기호로 매핑
  const getAttendanceSymbol = (type, reason) => {
    const symbolMap = {
      '결석-질병': '♡',
      '지각-질병': '#',
      '조퇴-질병': '＠',
      '결석-미인정': '🖤',
      '지각-미인정': '×',
      '조퇴-미인정': '◎',
      '결석-출석인정': '△',
      '지각-출석인정': '◁',
      '조퇴-출석인정': '▷'
    }
    return symbolMap[`${type}-${reason}`] || '?'
  }

  // 승인 상태 아이콘 반환 (배지 스타일)
  const getApprovalBadge = (status) => {
    const badgeMap = {
      '대기': { text: '대기', class: 'badge-pending' },
      '승인': { text: '승인', class: 'badge-approved' },
      '거부': { text: '거부', class: 'badge-rejected' },
      '수정됨': { text: '수정', class: 'badge-modified' }
    }
    return badgeMap[status] || badgeMap['대기']
  }

  // 출결 상태 표시 함수
  const renderAttendanceCell = (student, day) => {
    const key = `${student.id}-${day}`
    const record = attendanceMap.get(key)

    // 요일 계산 (주말 체크)
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const dayOfWeek = dayjs(dateStr).day()
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6

    let cellClass = 'attendance-cell'
    let content = ''
    let approvalBadge = null
    let documentIndicator = null

    if (record) {
      // 출결 기록이 있는 경우
      const statusClass = record.approval_status?.toLowerCase() || 'pending'
      cellClass += ` status-${statusClass}`

      // 9가지 조합을 기호로 표시
      content = getAttendanceSymbol(record.attendance_type, record.attendance_reason)

      // 승인 상태 배지
      const badge = getApprovalBadge(record.approval_status || '대기')
      approvalBadge = (
        <span className={`approval-badge ${badge.class}`}>
          {badge.text}
        </span>
      )

      // 서류 제출 표시 - 결석인 경우에만 표시
      if (record.attendance_type === '결석' && record.document_submitted !== undefined) {
        documentIndicator = (
          <span
            className={`doc-icon ${record.document_submitted ? 'doc-submitted' : 'doc-needed'}`}
            title={record.document_submitted ? '서류 제출 완료' : '서류 제출 필요'}
          >
            {record.document_submitted ? '☑' : '☐'}
          </span>
        )
      }
    }

    if (isWeekend) {
      cellClass += ' weekend'
    }

    return (
      <td
        key={`${student.id}-${day}`}
        className={cellClass}
        onClick={() => handleCellClick(student, day)}
        title={record ? `${record.attendance_type} (${record.attendance_reason}) - ${record.approval_status || '대기'}` : '출결 기록 없음'}
      >
        <div className="cell-wrapper">
          {approvalBadge}
          <div className="symbol-large">{content}</div>
          {documentIndicator}
        </div>
      </td>
    )
  }

  return (
    <div className="grid-container">
      <div style={{ marginBottom: '10px', padding: '12px', background: '#f8f9fa', borderRadius: '4px' }}>
        <div style={{ marginBottom: '8px' }}>
          <strong>📋 출결 기호 안내:</strong>
          <div style={{ marginTop: '5px' }}>
            <span style={{ marginRight: '15px' }}><strong>질병:</strong> ♡결석 #지각 ＠조퇴</span>
            <span style={{ marginRight: '15px' }}><strong>미인정:</strong> 🖤결석 ×지각 ◎조퇴</span>
            <span><strong>출석인정:</strong> △결석 ◁지각 ▷조퇴</span>
          </div>
        </div>
        <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #dee2e6', display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <div>
            <strong>승인 상태:</strong>
            <span style={{
              marginLeft: '8px',
              padding: '2px 8px',
              background: '#ffc107',
              borderRadius: '3px',
              fontSize: '11px',
              fontWeight: 'bold'
            }}>대기</span>
            <span style={{
              marginLeft: '4px',
              padding: '2px 8px',
              background: '#28a745',
              color: 'white',
              borderRadius: '3px',
              fontSize: '11px',
              fontWeight: 'bold'
            }}>승인</span>
            <span style={{
              marginLeft: '4px',
              padding: '2px 8px',
              background: '#dc3545',
              color: 'white',
              borderRadius: '3px',
              fontSize: '11px',
              fontWeight: 'bold'
            }}>거부</span>
            <span style={{
              marginLeft: '4px',
              padding: '2px 8px',
              background: '#17a2b8',
              color: 'white',
              borderRadius: '3px',
              fontSize: '11px',
              fontWeight: 'bold'
            }}>수정</span>
          </div>
          <div>
            <strong>서류 (결석만):</strong>
            <span style={{ marginLeft: '8px', color: '#dc3545', fontSize: '14px' }}>☐ 미제출</span>
            <span style={{ marginLeft: '8px', color: '#28a745', fontSize: '14px' }}>☑ 제출완료</span>
          </div>
        </div>
      </div>

      <table className="attendance-grid">
        <thead>
          <tr>
            <th>학생</th>
            {days.map(day => {
              const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
              const dayOfWeek = ['일', '월', '화', '수', '목', '금', '토'][dayjs(dateStr).day()]
              const isWeekend = dayjs(dateStr).day() === 0 || dayjs(dateStr).day() === 6

              return (
                <th key={day} className={isWeekend ? 'weekend' : ''}>
                  {day}
                  <br />
                  <small>{dayOfWeek}</small>
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {students.map(student => (
            <tr key={student.id}>
              <td>
                <strong>{student.student_number}.</strong> {student.name}
              </td>
              {days.map(day => renderAttendanceCell(student, day))}
            </tr>
          ))}
        </tbody>
      </table>

      {selectedCell && (
        <AttendanceModal
          selectedCell={selectedCell}
          onClose={handleCloseModal}
        />
      )}
    </div>
  )
}

export default AttendanceGrid
