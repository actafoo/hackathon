import axios from 'axios'

// 개발 환경에서는 프록시를 사용하고, 프로덕션에서는 환경 변수 사용
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 학생 관련 API
export const fetchStudents = async () => {
  const response = await api.get('/students/')
  return response.data
}

export const createStudent = async (studentData) => {
  const response = await api.post('/students/', studentData)
  return response.data
}

// 출결 관련 API
export const fetchMonthlyGrid = async (year, month) => {
  const response = await api.post('/attendance/monthly-grid', { year, month })
  return response.data
}

export const updateAttendanceRecord = async (recordId, updateData) => {
  const response = await api.put(`/attendance/${recordId}`, updateData)
  return response.data
}

export const approveAttendanceRecord = async (recordId, teacherName) => {
  const response = await api.post(`/attendance/${recordId}/approve`, null, {
    params: { teacher_name: teacherName }
  })
  return response.data
}

export const rejectAttendanceRecord = async (recordId, teacherName, reason) => {
  const response = await api.post(`/attendance/${recordId}/reject`, null, {
    params: { teacher_name: teacherName, reason }
  })
  return response.data
}

export const createAttendanceRecord = async (recordData) => {
  const response = await api.post('/attendance/', recordData)
  return response.data
}

export const deleteAttendanceRecord = async (recordId) => {
  const response = await api.delete(`/attendance/${recordId}`)
  return response.data
}

// 서류 제출 관련 API
export const fetchDocumentSubmissions = async (isSubmitted = null) => {
  const params = isSubmitted !== null ? { is_submitted: isSubmitted } : {}
  const response = await api.get('/documents/', { params })
  return response.data
}

export const markDocumentSubmitted = async (submissionId) => {
  const response = await api.post(`/documents/${submissionId}/mark-submitted`)
  return response.data
}

export const sendReminders = async () => {
  const response = await api.post('/documents/send-reminders')
  return response.data
}

export const sendIndividualReminder = async (studentId) => {
  const response = await api.post(`/documents/send-reminder/${studentId}`)
  return response.data
}

export const updateDocumentSubmission = async (submissionId, updateData) => {
  const response = await api.put(`/documents/${submissionId}`, updateData)
  return response.data
}

// 학부모 관련 API
export const fetchStudentParents = async (studentId) => {
  const response = await api.get(`/parents/student/${studentId}`)
  return response.data
}

export const createParent = async (parentData) => {
  const response = await api.post('/parents/', parentData)
  return response.data
}

export const updateParent = async (parentId, updateData) => {
  const response = await api.put(`/parents/${parentId}`, updateData)
  return response.data
}

export const deleteParent = async (parentId) => {
  const response = await api.delete(`/parents/${parentId}`)
  return response.data
}

export const toggleParentActive = async (parentId) => {
  const response = await api.post(`/parents/${parentId}/toggle-active`)
  return response.data
}

export default api
