// 后端 API 客户端封装。

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"

export interface Course {
  id: number
  title: string
  status: string
  status_message: string | null
  progress_percent: number
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
  id?: number
  role: "user" | "assistant"
  content: string
  scope?: "course" | "all"
  sources?: Source[] | null
  created_at?: string
  course_id?: number
}

export interface ChatResponse {
  course_id: number
  answer: string
  sources: Source[] | null
  answer_message_id?: number
}

export interface Settings {
  chat_model: string
  chat_api_key: string
  summary_model: string
  summary_api_key: string
  vision_model: string
  vision_api_key: string
  enable_vision: boolean
  is_configured: boolean
  restart_required?: boolean
  main_api_key?: string
}

export interface HistoryItem {
  id: number
  course_id: number
  role: "user" | "assistant"
  content: string
  scope: "course" | "all"
  sources: Source[] | null
  created_at: string
  course_title?: string
}

export interface TranscriptDebug {
  id: number
  start_time: number
  end_time: number
  text: string
  confidence: number | null
}

export interface FrameDebug {
  id: number
  timestamp: number
  image_path: string
  thumbnail_path: string | null
  ocr_text: string | null
  vision_desc: string | null
}

export interface SummaryDebug {
  outline: string | null
  abstract: string | null
  lecture_notes: string | null
}

export interface ChatDebug {
  message_id: number
  course_id?: number
  course_title?: string | null
  question: string
  answer: string
  model: string
  prompt: string
  context: string
  raw_answer: string
  sources: Source[] | null
  scope?: "course" | "all"
  created_at?: string
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    cache: "no-store",
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

export async function getSettings(): Promise<Settings> {
  return request<Settings>("/api/settings")
}

export async function saveSettings(payload: Partial<Settings>): Promise<Settings> {
  return request<Settings>("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function listChatHistory(): Promise<HistoryItem[]> {
  return request<HistoryItem[]>("/api/history")
}

export async function deleteChatHistory(messageId: number): Promise<void> {
  await request(`/api/history/${messageId}`, { method: "DELETE" })
}

export async function getCourseTranscriptsDebug(courseId: number): Promise<TranscriptDebug[]> {
  return request<TranscriptDebug[]>(`/api/courses/${courseId}/debug/transcripts`)
}

export async function getCourseFramesDebug(courseId: number): Promise<FrameDebug[]> {
  return request<FrameDebug[]>(`/api/courses/${courseId}/debug/frames`)
}

export async function getCourseSummaryDebug(courseId: number): Promise<SummaryDebug> {
  return request<SummaryDebug>(`/api/courses/${courseId}/debug/summary`)
}

export async function getChatDebug(messageId: number): Promise<ChatDebug> {
  return request<ChatDebug>(`/api/chat/${messageId}/debug`)
}
