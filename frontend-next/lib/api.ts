// 后端 API 客户端封装。

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"

export interface Course {
  id: number
  title: string
  status: string
  status_message: string | null
  duration: number | null
  created_at: string
}

export interface CourseDetail extends Course {
  video_url: string
  updated_at: string
}

export interface Summary {
  course_id: number
  outline: string | null
  abstract: string | null
  lecture_notes: string | null
}

export interface Source {
  type: string
  timestamp: number
  text: string
  course_id: number | null
  course_title: string | null
  frame_id: number | null
  transcript_id: number | null
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  sources?: Source[] | null
  created_at?: string
}

export interface ChatResponse {
  course_id: number
  answer: string
  sources: Source[] | null
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options?.headers || {}),
    },
  })
  if (!response.ok) {
    const text = await response.text().catch(() => "")
    throw new Error(`HTTP ${response.status}: ${text}`)
  }
  return response.json() as Promise<T>
}

export async function listCourses(): Promise<Course[]> {
  return request<Course[]>("/api/courses")
}

export async function getCourse(id: number): Promise<CourseDetail> {
  return request<CourseDetail>(`/api/courses/${id}`)
}

export async function uploadCourse(formData: FormData): Promise<{ id: number; title: string; status: string; created_at: string }> {
  return request<{ id: number; title: string; status: string; created_at: string }>("/api/courses/upload", {
    method: "POST",
    body: formData,
  })
}

export async function deleteCourse(id: number): Promise<void> {
  await request(`/api/courses/${id}`, { method: "DELETE" })
}

export async function reprocessCourse(id: number): Promise<void> {
  await request(`/api/courses/${id}/reprocess`, { method: "POST" })
}

export async function getSummary(courseId: number): Promise<Summary> {
  return request<Summary>(`/api/summaries/${courseId}`)
}

export async function askQuestion(courseId: number, question: string, scope: "course" | "all"): Promise<ChatResponse> {
  return request<ChatResponse>(`/api/chat/${courseId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, scope }),
  })
}

export async function getChatHistory(courseId: number): Promise<ChatMessage[]> {
  return request<ChatMessage[]>(`/api/chat/${courseId}/history`)
}

export function getVideoUrl(courseId: number): string {
  return `${API_BASE}/api/courses/${courseId}/video`
}
