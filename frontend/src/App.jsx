import React, { useState, useEffect } from 'react'
import AttendanceGrid from './components/AttendanceGrid'
import StudentManagement from './components/StudentManagement'
import { fetchMonthlyGrid, sendReminders } from './services/api'
import dayjs from 'dayjs'

function App() {
  const [year, setYear] = useState(dayjs().year())
  const [month, setMonth] = useState(dayjs().month() + 1)
  const [gridData, setGridData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showStudentManagement, setShowStudentManagement] = useState(false)

  // 통계 계산
  const stats = gridData ? {
    totalStudents: gridData.students.length,
    totalRecords: gridData.attendance_data.length,
    pendingApprovals: gridData.attendance_data.filter(r => r.approval_status === '대기').length,
    approvedRecords: gridData.attendance_data.filter(r => r.approval_status === '승인').length,
    documentsNeeded: gridData.attendance_data.filter(r =>
      r.attendance_type === '결석' && r.document_submitted === false
    ).length
  } : null

  const loadGridData = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchMonthlyGrid(year, month)
      setGridData(data)
    } catch (err) {
      setError('데이터를 불러오는 중 오류가 발생했습니다: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadGridData()
  }, [year, month])

  const handleSendReminders = async () => {
    if (confirm('서류 미제출 학생들에게 독려 메시지를 발송하시겠습니까?')) {
      try {
        const result = await sendReminders()
        alert(`독려 메시지 발송 완료\n성공: ${result.sent_count}건, 실패: ${result.failed_count}건`)
        loadGridData()
      } catch (err) {
        alert('독려 메시지 발송 중 오류가 발생했습니다: ' + err.message)
      }
    }
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="app">
      {/* 헤더 */}
      <div className="header">
        <div className="header-content">
          <div className="header-title">
            <h1>📋 출결 관리 시스템</h1>
            <p className="header-subtitle">학생 출결 및 서류 관리 대시보드</p>
          </div>
          <div className="month-selector">
            <select value={year} onChange={(e) => setYear(Number(e.target.value))}>
              {[2024, 2025, 2026].map(y => (
                <option key={y} value={y}>{y}년</option>
              ))}
            </select>
            <select value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                <option key={m} value={m}>{m}월</option>
              ))}
            </select>
            <button className="btn-query" onClick={loadGridData}>
              🔍 조회
            </button>
          </div>
        </div>
      </div>

      {/* 통계 카드 */}
      {stats && !loading && (
        <div className="stats-container">
          <div className="stat-card stat-card-primary">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <div className="stat-value">{stats.totalStudents}</div>
              <div className="stat-label">전체 학생</div>
            </div>
          </div>

          <div className="stat-card stat-card-info">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-value">{stats.totalRecords}</div>
              <div className="stat-label">이번 달 출결</div>
            </div>
          </div>

          <div className="stat-card stat-card-warning">
            <div className="stat-icon">⏳</div>
            <div className="stat-content">
              <div className="stat-value">{stats.pendingApprovals}</div>
              <div className="stat-label">승인 대기</div>
            </div>
          </div>

          <div className="stat-card stat-card-success">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <div className="stat-value">{stats.approvedRecords}</div>
              <div className="stat-label">승인 완료</div>
            </div>
          </div>

          <div className="stat-card stat-card-danger">
            <div className="stat-icon">📄</div>
            <div className="stat-content">
              <div className="stat-value">{stats.documentsNeeded}</div>
              <div className="stat-label">서류 미제출</div>
            </div>
          </div>
        </div>
      )}

      {/* 액션 바 */}
      <div className="actions-bar">
        <button className="btn btn-success" onClick={() => setShowStudentManagement(true)}>
          <span className="btn-icon">👥</span>
          학생 관리
        </button>
        <button className="btn btn-primary" onClick={handleSendReminders}>
          <span className="btn-icon">📤</span>
          서류 독려 메시지
        </button>
        <button className="btn btn-secondary" onClick={loadGridData}>
          <span className="btn-icon">🔄</span>
          새로고침
        </button>
        <button className="btn btn-secondary" onClick={handlePrint}>
          <span className="btn-icon">🖨️</span>
          출결표 인쇄
        </button>
      </div>

      {loading && (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>데이터 로딩 중...</p>
        </div>
      )}
      {error && <div className="error">⚠️ {error}</div>}
      {gridData && !loading && (
        <AttendanceGrid
          year={year}
          month={month}
          students={gridData.students}
          attendanceData={gridData.attendance_data}
          onUpdate={loadGridData}
        />
      )}

      {showStudentManagement && (
        <StudentManagement onClose={() => setShowStudentManagement(false)} />
      )}
    </div>
  )
}

export default App
