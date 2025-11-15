import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom'
import { fetchStudents, createStudent, fetchStudentParents, createParent, deleteParent, toggleParentActive } from '../services/api'

const StudentManagement = ({ onClose }) => {
  const [students, setStudents] = useState([])
  const [newStudent, setNewStudent] = useState({
    name: '',
    student_number: '',
    telegram_id: '',
    phone: ''
  })
  const [selectedStudent, setSelectedStudent] = useState(null)
  const [parents, setParents] = useState([])
  const [newParent, setNewParent] = useState({
    telegram_id: '',
    parent_name: '',
    relation: ''
  })
  const [loading, setLoading] = useState(false)

  // 모달 열릴 때 body 스크롤 방지
  useEffect(() => {
    document.body.classList.add('modal-open')
    return () => {
      document.body.classList.remove('modal-open')
    }
  }, [])

  useEffect(() => {
    loadStudents()
  }, [])

  useEffect(() => {
    if (selectedStudent) {
      loadParents(selectedStudent.id)
    }
  }, [selectedStudent])

  const loadStudents = async () => {
    try {
      const data = await fetchStudents()
      setStudents(data)
    } catch (error) {
      alert('학생 목록을 불러오는데 실패했습니다: ' + error.message)
    }
  }

  const loadParents = async (studentId) => {
    try {
      const data = await fetchStudentParents(studentId)
      setParents(data)
    } catch (error) {
      alert('학부모 목록을 불러오는데 실패했습니다: ' + error.message)
    }
  }

  const handleAddStudent = async (e) => {
    e.preventDefault()
    if (!newStudent.name || !newStudent.student_number) {
      alert('이름과 출석번호는 필수입니다.')
      return
    }

    setLoading(true)
    try {
      // 빈 문자열을 null로 변환하여 전송
      const studentData = {
        name: newStudent.name,
        student_number: Number(newStudent.student_number),
        telegram_id: newStudent.telegram_id || null,
        phone: newStudent.phone || null
      }

      await createStudent(studentData)
      alert('학생이 추가되었습니다.')
      setNewStudent({ name: '', student_number: '', telegram_id: '', phone: '' })
      loadStudents()
    } catch (error) {
      alert('학생 추가 실패: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAddParent = async (e) => {
    e.preventDefault()
    if (!newParent.telegram_id) {
      alert('텔레그램 ID는 필수입니다.')
      return
    }

    setLoading(true)
    try {
      await createParent({
        student_id: selectedStudent.id,
        ...newParent
      })
      alert('학부모가 추가되었습니다.')
      setNewParent({ telegram_id: '', parent_name: '', relation: '' })
      loadParents(selectedStudent.id)
    } catch (error) {
      alert('학부모 추가 실패: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteParent = async (parentId) => {
    if (!confirm('이 학부모를 삭제하시겠습니까?')) return

    try {
      await deleteParent(parentId)
      alert('학부모가 삭제되었습니다.')
      loadParents(selectedStudent.id)
    } catch (error) {
      alert('학부모 삭제 실패: ' + error.message)
    }
  }

  const handleToggleParentActive = async (parentId) => {
    try {
      await toggleParentActive(parentId)
      loadParents(selectedStudent.id)
    } catch (error) {
      alert('학부모 상태 변경 실패: ' + error.message)
    }
  }

  const modalContent = (
    <div className="modal" onClick={onClose}>
      <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          👥 학생 및 학부모 관리
        </div>

        <div className="modal-body">
          {/* 새 학생 추가 폼 */}
          <div style={{ marginBottom: '24px', padding: '16px', background: '#f8f9fa', borderRadius: '8px' }}>
            <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>새 학생 추가</h3>
            <form onSubmit={handleAddStudent}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label>이름 *</label>
                  <input
                    type="text"
                    value={newStudent.name}
                    onChange={(e) => setNewStudent({ ...newStudent, name: e.target.value })}
                    placeholder="홍길동"
                    required
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label>출석번호 *</label>
                  <input
                    type="number"
                    value={newStudent.student_number}
                    onChange={(e) => setNewStudent({ ...newStudent, student_number: e.target.value })}
                    placeholder="1"
                    required
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label>텔레그램 ID (선택)</label>
                  <input
                    type="text"
                    value={newStudent.telegram_id}
                    onChange={(e) => setNewStudent({ ...newStudent, telegram_id: e.target.value })}
                    placeholder="user001"
                  />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label>전화번호 (선택)</label>
                  <input
                    type="text"
                    value={newStudent.phone}
                    onChange={(e) => setNewStudent({ ...newStudent, phone: e.target.value })}
                    placeholder="010-1234-5678"
                  />
                </div>
              </div>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                ➕ 학생 추가
              </button>
            </form>
          </div>

          {/* 학생 목록 및 학부모 관리 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {/* 학생 목록 */}
            <div>
              <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>등록된 학생 목록 ({students.length}명)</h3>
              <div style={{ maxHeight: '400px', overflowY: 'auto', border: '1px solid #ddd', borderRadius: '4px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead style={{ position: 'sticky', top: 0, background: '#f8f9fa' }}>
                    <tr>
                      <th style={{ padding: '8px', borderBottom: '1px solid #ddd', textAlign: 'left' }}>번호</th>
                      <th style={{ padding: '8px', borderBottom: '1px solid #ddd', textAlign: 'left' }}>이름</th>
                      <th style={{ padding: '8px', borderBottom: '1px solid #ddd', textAlign: 'center' }}>학부모</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map(student => (
                      <tr
                        key={student.id}
                        onClick={() => setSelectedStudent(student)}
                        style={{
                          cursor: 'pointer',
                          background: selectedStudent?.id === student.id ? '#e3f2fd' : 'transparent'
                        }}
                      >
                        <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{student.student_number}</td>
                        <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                          <strong>{student.name}</strong>
                        </td>
                        <td style={{ padding: '8px', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                          <button
                            className="btn btn-small"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedStudent(student)
                            }}
                          >
                            관리
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 학부모 관리 */}
            <div>
              {selectedStudent ? (
                <>
                  <h3 style={{ marginBottom: '12px', fontSize: '16px' }}>
                    {selectedStudent.name} 학생의 학부모 ({parents.length}명)
                  </h3>

                  {/* 학부모 추가 폼 */}
                  <div style={{ marginBottom: '16px', padding: '12px', background: '#f0f7ff', borderRadius: '4px' }}>
                    <h4 style={{ marginBottom: '8px', fontSize: '14px' }}>학부모 추가</h4>
                    <form onSubmit={handleAddParent}>
                      <div className="form-group" style={{ marginBottom: '8px' }}>
                        <label style={{ fontSize: '12px' }}>텔레그램 ID *</label>
                        <input
                          type="text"
                          value={newParent.telegram_id}
                          onChange={(e) => setNewParent({ ...newParent, telegram_id: e.target.value })}
                          placeholder="123456789"
                          required
                          style={{ fontSize: '12px' }}
                        />
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label style={{ fontSize: '12px' }}>이름 (선택)</label>
                          <input
                            type="text"
                            value={newParent.parent_name}
                            onChange={(e) => setNewParent({ ...newParent, parent_name: e.target.value })}
                            placeholder="홍아무개"
                            style={{ fontSize: '12px' }}
                          />
                        </div>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label style={{ fontSize: '12px' }}>관계 (선택)</label>
                          <input
                            type="text"
                            value={newParent.relation}
                            onChange={(e) => setNewParent({ ...newParent, relation: e.target.value })}
                            placeholder="부, 모, 조부모 등"
                            style={{ fontSize: '12px' }}
                          />
                        </div>
                      </div>
                      <button type="submit" className="btn btn-small btn-primary" disabled={loading}>
                        ➕ 추가
                      </button>
                    </form>
                  </div>

                  {/* 학부모 목록 */}
                  <div style={{ maxHeight: '280px', overflowY: 'auto', border: '1px solid #ddd', borderRadius: '4px' }}>
                    {parents.length === 0 ? (
                      <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
                        등록된 학부모가 없습니다.
                        <br />
                        텔레그램으로 메시지를 보내면 자동으로 등록됩니다.
                      </div>
                    ) : (
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                        <thead style={{ position: 'sticky', top: 0, background: '#f8f9fa' }}>
                          <tr>
                            <th style={{ padding: '6px', borderBottom: '1px solid #ddd', textAlign: 'left' }}>텔레그램 ID</th>
                            <th style={{ padding: '6px', borderBottom: '1px solid #ddd', textAlign: 'left' }}>이름</th>
                            <th style={{ padding: '6px', borderBottom: '1px solid #ddd', textAlign: 'left' }}>관계</th>
                            <th style={{ padding: '6px', borderBottom: '1px solid #ddd', textAlign: 'center' }}>상태</th>
                            <th style={{ padding: '6px', borderBottom: '1px solid #ddd', textAlign: 'center' }}>관리</th>
                          </tr>
                        </thead>
                        <tbody>
                          {parents.map(parent => (
                            <tr key={parent.id} style={{ opacity: parent.is_active ? 1 : 0.5 }}>
                              <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>
                                {parent.telegram_id}
                                {parent.auto_registered && <span style={{ fontSize: '10px', color: '#666', marginLeft: '4px' }}>(자동)</span>}
                              </td>
                              <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>
                                {parent.parent_name || '-'}
                              </td>
                              <td style={{ padding: '6px', borderBottom: '1px solid #eee' }}>
                                {parent.relation || '-'}
                              </td>
                              <td style={{ padding: '6px', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                                <span style={{
                                  fontSize: '11px',
                                  padding: '2px 6px',
                                  borderRadius: '3px',
                                  background: parent.is_active ? '#d4edda' : '#f8d7da',
                                  color: parent.is_active ? '#155724' : '#721c24'
                                }}>
                                  {parent.is_active ? '활성' : '비활성'}
                                </span>
                              </td>
                              <td style={{ padding: '6px', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                                <button
                                  className="btn btn-small"
                                  onClick={() => handleToggleParentActive(parent.id)}
                                  style={{ fontSize: '11px', padding: '4px 8px', marginRight: '4px' }}
                                >
                                  {parent.is_active ? '비활성화' : '활성화'}
                                </button>
                                <button
                                  className="btn btn-small"
                                  onClick={() => handleDeleteParent(parent.id)}
                                  style={{ fontSize: '11px', padding: '4px 8px', background: '#dc3545', color: 'white' }}
                                >
                                  삭제
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </>
              ) : (
                <div style={{ padding: '40px 20px', textAlign: 'center', color: '#999', border: '1px dashed #ddd', borderRadius: '4px' }}>
                  왼쪽에서 학생을 선택하면
                  <br />
                  학부모 정보를 관리할 수 있습니다.
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose}>
            닫기
          </button>
        </div>
      </div>
    </div>
  )

  // Portal을 사용하여 모달을 document.body에 직접 렌더링
  return ReactDOM.createPortal(modalContent, document.body)
}

export default StudentManagement
