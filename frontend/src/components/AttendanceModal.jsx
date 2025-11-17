import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom'
import {
  updateAttendanceRecord,
  approveAttendanceRecord,
  rejectAttendanceRecord,
  createAttendanceRecord,
  markDocumentSubmitted,
  deleteAttendanceRecord,
  sendIndividualReminder
} from '../services/api'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

const AttendanceModal = ({ selectedCell, onClose }) => {
  const { student, day, date, record } = selectedCell

  const [attendanceType, setAttendanceType] = useState(record?.attendance_type || '결석')
  const [attendanceReason, setAttendanceReason] = useState(record?.attendance_reason || '질병')
  const [teacherName, setTeacherName] = useState('교사')
  const [modificationReason, setModificationReason] = useState('')
  const [loading, setLoading] = useState(false)
  const [documents, setDocuments] = useState([])

  // 모달 열릴 때 body 스크롤 방지
  useEffect(() => {
    document.body.classList.add('modal-open')
    return () => {
      document.body.classList.remove('modal-open')
    }
  }, [])

  // 서류 정보 로드
  useEffect(() => {
    if (record && record.record_id) {
      loadDocuments()
    }
  }, [record])

  const loadDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents/`, {
        params: { student_id: student.id }
      })
      // 이 출결 기록과 연결된 서류만 필터링
      const relatedDocs = response.data.filter(doc => {
        // attendance_record_id로 직접 매칭
        if (doc.attendance_record_id === record.record_id) {
          return true
        }
        // 날짜로 매칭 (날짜만 비교, 시간은 무시)
        const docDate = new Date(doc.date).toISOString().split('T')[0]
        const recordDate = new Date(record.date).toISOString().split('T')[0]
        return docDate === recordDate && doc.student_id === student.id
      })
      setDocuments(relatedDocs)
    } catch (error) {
      console.error('서류 정보 로드 실패:', error)
    }
  }

  const handleMarkDocumentSubmitted = async (docId) => {
    if (!confirm('이 서류를 제출 완료로 표시하시겠습니까?')) return

    try {
      await markDocumentSubmitted(docId)
      alert('서류가 제출 완료로 표시되었습니다.')
      loadDocuments() // 새로고침
    } catch (error) {
      alert('오류가 발생했습니다: ' + error.message)
    }
  }

  const handleSendReminder = async () => {
    if (!confirm(`${student.name} 학생 학부모님께 서류 제출 독려 메시지를 발송하시겠습니까?`)) return

    try {
      const result = await sendIndividualReminder(student.id)
      alert(`독려 메시지 발송 완료!\n성공: ${result.sent_count}건, 실패: ${result.failed_count}건`)
    } catch (error) {
      alert('오류가 발생했습니다: ' + error.message)
    }
  }

  // 9가지 조합을 기호로 표시
  const getSymbol = (type, reason) => {
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

  // 승인 상태 아이콘
  const getStatusIcon = (status) => {
    const iconMap = {
      '대기': '⏳',
      '승인': '✓',
      '거부': '✗',
      '수정됨': '✏️'
    }
    return iconMap[status] || '⏳'
  }

  // 승인 상태별 배경색
  const getStatusBackground = (status) => {
    const colorMap = {
      '대기': '#fff3cd',
      '승인': '#d4edda',
      '거부': '#f8d7da',
      '수정됨': '#e2e3e5'
    }
    return colorMap[status] || '#fff3cd'
  }

  // 승인 상태별 테두리 색
  const getStatusBorderColor = (status) => {
    const colorMap = {
      '대기': '#ffc107',
      '승인': '#28a745',
      '거부': '#dc3545',
      '수정됨': '#6c757d'
    }
    return colorMap[status] || '#ffc107'
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      if (record) {
        // 기존 기록 수정
        await updateAttendanceRecord(record.record_id, {
          attendance_type: attendanceType,
          attendance_reason: attendanceReason,
          approval_status: '수정됨',
          modified_by: teacherName,
          modification_reason: modificationReason || undefined
        })
        alert('출결 기록이 수정되었습니다.')
      } else {
        // 새 기록 생성
        await createAttendanceRecord({
          student_id: student.id,
          date: new Date(date).toISOString(),
          attendance_type: attendanceType,
          attendance_reason: attendanceReason
        })
        alert('출결 기록이 생성되었습니다.')
      }
      onClose()
    } catch (error) {
      alert('오류가 발생했습니다: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!record) return
    setLoading(true)
    try {
      await approveAttendanceRecord(record.record_id, teacherName)
      alert('출결 기록이 승인되었습니다.')
      onClose()
    } catch (error) {
      alert('오류가 발생했습니다: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async () => {
    if (!record) return
    if (!confirm('이 출결 기록을 거부하시겠습니까?')) return

    setLoading(true)
    try {
      await rejectAttendanceRecord(record.record_id, teacherName, modificationReason)
      alert('출결 기록이 거부되었습니다.')
      onClose()
    } catch (error) {
      alert('오류가 발생했습니다: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!record) return
    if (!confirm('이 출결 기록을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return

    setLoading(true)
    try {
      await deleteAttendanceRecord(record.record_id)
      alert('출결 기록이 삭제되었습니다.')
      onClose()
    } catch (error) {
      alert('오류가 발생했습니다: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const modalContent = (
    <div className="modal" onClick={onClose}>
      <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          출결 기록 {record ? '수정' : '생성'}
        </div>

        <div className="modal-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* 왼쪽 열 - 기본 정보 및 출결 설정 */}
            <div>
              <div style={{ marginBottom: '16px', padding: '12px', background: '#f8f9fa', borderRadius: '8px' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px' }}>
                  {student.name} ({student.student_number}번)
                </div>
                <div style={{ color: '#666', fontSize: '14px' }}>날짜: {date}</div>
              </div>

              {record && (
                <div style={{
                  marginBottom: '16px',
                  padding: '12px',
                  background: getStatusBackground(record.approval_status),
                  borderRadius: '8px',
                  border: `2px solid ${getStatusBorderColor(record.approval_status)}`
                }}>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '4px' }}>
                    {getStatusIcon(record.approval_status)} 승인 상태: {record.approval_status || '대기'}
                  </div>
                  <small style={{ color: '#666' }}>원본 메시지: {record.original_message || '없음'}</small>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label>출결 타입</label>
                  <select value={attendanceType} onChange={(e) => setAttendanceType(e.target.value)}>
                    <option value="결석">결석</option>
                    <option value="지각">지각</option>
                    <option value="조퇴">조퇴</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>출결 사유</label>
                  <select value={attendanceReason} onChange={(e) => setAttendanceReason(e.target.value)}>
                    <option value="질병">질병</option>
                    <option value="미인정">미인정</option>
                    <option value="출석인정">출석인정</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '16px', padding: '12px', background: '#fff3cd', borderRadius: '8px', textAlign: 'center' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>선택한 출결 상태</div>
                <div style={{ fontSize: '32px', marginBottom: '4px' }}>{getSymbol(attendanceType, attendanceReason)}</div>
                <div style={{ fontSize: '13px', color: '#666' }}>{attendanceType} - {attendanceReason}</div>
              </div>

              <div className="form-group">
                <label>교사 이름</label>
                <input
                  type="text"
                  value={teacherName}
                  onChange={(e) => setTeacherName(e.target.value)}
                  placeholder="교사 이름 입력"
                />
              </div>

              <div className="form-group">
                <label>수정/거부 사유 (선택)</label>
                <textarea
                  value={modificationReason}
                  onChange={(e) => setModificationReason(e.target.value)}
                  placeholder="수정 또는 거부 사유를 입력하세요"
                  rows="4"
                />
              </div>
            </div>

            {/* 오른쪽 열 - 서류 제출 상태 */}
            <div>
              {record && documents.length > 0 ? (
                <div style={{ padding: '12px', background: '#f0f7ff', borderRadius: '8px', border: '1px solid #b3d9ff' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <strong style={{ fontSize: '16px' }}>📎 서류 제출 상태</strong>
                    {documents.some(doc => !doc.is_submitted) && (
                      <button
                        className="btn btn-warning"
                        onClick={handleSendReminder}
                        style={{ fontSize: '12px', padding: '6px 12px' }}
                      >
                        📤 독려 메시지 발송
                      </button>
                    )}
                  </div>
                  {documents.map(doc => (
                    <div key={doc.id} style={{
                      padding: '12px',
                      marginBottom: '12px',
                      background: doc.is_submitted ? '#d4edda' : '#fff3cd',
                      borderRadius: '8px',
                      border: `2px solid ${doc.is_submitted ? '#28a745' : '#ffc107'}`
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>
                            {doc.document_type || '출결 서류'}
                          </div>
                          <div style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>
                            날짜: {new Date(doc.date).toLocaleDateString('ko-KR')}
                          </div>
                          {doc.is_submitted && doc.submitted_at && (
                            <div style={{ fontSize: '12px', color: '#28a745', fontWeight: 'bold' }}>
                              ✓ 제출 완료: {new Date(doc.submitted_at).toLocaleDateString('ko-KR')}
                            </div>
                          )}
                          {doc.file_path && (
                            <div style={{ marginTop: '12px' }}>
                              <a
                                href={`http://localhost:8000/uploads/${doc.file_path}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ fontSize: '13px', color: '#007bff', textDecoration: 'none', fontWeight: 'bold' }}
                              >
                                📷 서류 이미지 보기
                              </a>
                              <div style={{ marginTop: '8px' }}>
                                <img
                                  src={`http://localhost:8000/uploads/${doc.file_path}`}
                                  alt="제출 서류"
                                  style={{
                                    maxWidth: '100%',
                                    maxHeight: '300px',
                                    borderRadius: '8px',
                                    border: '2px solid #ddd',
                                    cursor: 'pointer',
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                                  }}
                                  onClick={() => window.open(`http://localhost:8000/uploads/${doc.file_path}`, '_blank')}
                                />
                              </div>
                            </div>
                          )}
                        </div>
                        {!doc.is_submitted && (
                          <button
                            className="btn btn-success"
                            onClick={() => handleMarkDocumentSubmitted(doc.id)}
                            style={{ fontSize: '12px', padding: '6px 12px', flexShrink: 0 }}
                          >
                            제출 완료 표시
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{
                  padding: '40px 20px',
                  background: '#f8f9fa',
                  borderRadius: '8px',
                  textAlign: 'center',
                  color: '#999',
                  border: '2px dashed #ddd'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '12px' }}>📄</div>
                  <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>서류 제출 내역 없음</div>
                  <div style={{ fontSize: '12px' }}>결석 기록이 있으면 서류 제출 현황이 여기에 표시됩니다.</div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="modal-actions">
          {record && (
            <>
              <button
                className="btn btn-success"
                onClick={handleApprove}
                disabled={loading}
              >
                ✓ 승인
              </button>
              <button
                className="btn btn-danger"
                onClick={handleReject}
                disabled={loading}
              >
                ✗ 거부
              </button>
              <button
                className="btn btn-danger"
                onClick={handleDelete}
                disabled={loading}
                style={{ marginLeft: 'auto' }}
              >
                🗑️ 삭제
              </button>
            </>
          )}
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={loading}
          >
            💾 저장
          </button>
          <button
            className="btn btn-secondary"
            onClick={onClose}
            disabled={loading}
          >
            취소
          </button>
        </div>
      </div>
    </div>
  )

  // Portal을 사용하여 모달을 document.body에 직접 렌더링
  return ReactDOM.createPortal(modalContent, document.body)
}

export default AttendanceModal
