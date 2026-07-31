// 后端 API 客户端封装。

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"

// 问答范围：单课程 / 全部课程 / 学习集（自定义课程组合）
export type ChatScope = "course" | "all" | "set"

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
  scope?: ChatScope
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
  scope: ChatScope
  sources: Source[] | null
  created_at: string
  course_title?: string
  /** set/all 实际涉及的课程 id 与名称（优先于锚点 course_title 显示） */
  course_ids?: number[]
  course_titles?: string[]
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
  scope?: ChatScope
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

export async function askQuestion(
  courseId: number,
  question: string,
  scope: ChatScope,
  courseIds?: number[],
): Promise<ChatResponse> {
  return request<ChatResponse>(`/api/chat/${courseId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, scope, course_ids: courseIds ?? null }),
  })
}

// ---- 学习集（自定义课程组合）----

export interface StudySet {
  id: number
  name: string
  course_ids: number[]
  course_titles: string[]
  created_at: string
}

export async function listStudySets(): Promise<StudySet[]> {
  return request<StudySet[]>("/api/study-sets")
}

export async function createStudySet(name: string, courseIds: number[]): Promise<StudySet> {
  return request<StudySet>("/api/study-sets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, course_ids: courseIds }),
  })
}

export async function updateStudySet(
  id: number,
  payload: { name?: string; course_ids?: number[] },
): Promise<StudySet> {
  return request<StudySet>(`/api/study-sets/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function deleteStudySet(id: number): Promise<void> {
  await request(`/api/study-sets/${id}`, { method: "DELETE" })
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

// ---- 测验（Question）----

export interface Question {
  id: number
  type: "choice" | "judge"
  question: string
  options: string[] | null
  answer: string
  explanation: string | null
  source_course_id: number | null
  source_timestamp: number | null
  /** 最近一次作答进度（断点续答）；未作答为 null */
  last_answer?: string | null
  last_correct?: boolean | null
}

export interface QuizGenerateResponse {
  generated: number
  total: number
}

export interface QuizAnswerResponse {
  question_id: number
  correct: boolean
  answer: string
  explanation: string | null
}

/** 错题本条目：历史答错记录，连续答对 N 次才标"已掌握"，记录保留 */
export interface WrongQuestion extends Question {
  mastered: boolean
  wrong_count: number
  /** 自最近一次答错起的连续答对数（掌握进度） */
  streak: number
  /** 连续答对多少次算掌握 */
  master_streak: number
}

/** 范围参数：课程或学习集二选一 */
export interface QuizScope {
  courseId?: number
  studySetId?: number
}

function scopeQuery(scope: QuizScope): string {
  if (scope.studySetId != null) return `study_set_id=${scope.studySetId}`
  return `course_id=${scope.courseId}`
}

export async function generateQuiz(scope: QuizScope, count = 12): Promise<QuizGenerateResponse> {
  return request<QuizGenerateResponse>("/api/quiz/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      course_id: scope.courseId ?? null,
      study_set_id: scope.studySetId ?? null,
      count,
    }),
  })
}

export async function listQuiz(scope: QuizScope): Promise<Question[]> {
  return request<Question[]>(`/api/quiz?${scopeQuery(scope)}`)
}

export async function listWrongQuiz(scope: QuizScope): Promise<WrongQuestion[]> {
  return request<WrongQuestion[]>(`/api/quiz/wrong?${scopeQuery(scope)}`)
}

export async function clearWrongQuiz(scope: QuizScope): Promise<void> {
  await request(`/api/quiz/wrong?${scopeQuery(scope)}`, { method: "DELETE" })
}

export async function submitQuizAnswer(questionId: number, answer: string): Promise<QuizAnswerResponse> {
  return request<QuizAnswerResponse>(`/api/quiz/${questionId}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer }),
  })
}

export async function clearQuiz(scope: QuizScope): Promise<void> {
  await request(`/api/quiz?${scopeQuery(scope)}`, { method: "DELETE" })
}

// ---- 闪卡（Flashcard）----

export type Familiarity = "known" | "fuzzy" | "unknown"

export interface Flashcard {
  id: number
  front: string
  back: string
  familiarity: Familiarity
  source_course_id: number | null
  source_timestamp: number | null
}

export interface FlashcardGenerateResponse {
  generated: number
  total: number
}

export interface FlashcardStats {
  total: number
  known: number
  fuzzy: number
  unknown: number
}

export async function generateFlashcards(scope: QuizScope, count = 15): Promise<FlashcardGenerateResponse> {
  return request<FlashcardGenerateResponse>("/api/flashcards/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      course_id: scope.courseId ?? null,
      study_set_id: scope.studySetId ?? null,
      count,
    }),
  })
}

export async function listFlashcards(scope: QuizScope): Promise<Flashcard[]> {
  return request<Flashcard[]>(`/api/flashcards?${scopeQuery(scope)}`)
}

export async function getFlashcardStats(scope: QuizScope): Promise<FlashcardStats> {
  return request<FlashcardStats>(`/api/flashcards/stats?${scopeQuery(scope)}`)
}

export async function setFlashcardFamiliarity(flashcardId: number, familiarity: Familiarity): Promise<Flashcard> {
  return request<Flashcard>(`/api/flashcards/${flashcardId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ familiarity }),
  })
}

export async function clearFlashcards(scope: QuizScope): Promise<void> {
  await request(`/api/flashcards?${scopeQuery(scope)}`, { method: "DELETE" })
}

// ---- 笔记/书签（Note）----

export type NoteKind = "note" | "bookmark"

export interface Note {
  id: number
  course_id: number
  kind: NoteKind
  content: string
  timestamp: number
  created_at: string
  updated_at: string
}

export async function listNotes(courseId: number): Promise<Note[]> {
  return request<Note[]>(`/api/notes?course_id=${courseId}`)
}

export async function createNote(payload: {
  course_id: number
  kind: NoteKind
  content?: string
  timestamp: number
}): Promise<Note> {
  return request<Note>("/api/notes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function updateNote(noteId: number, content: string): Promise<Note> {
  return request<Note>(`/api/notes/${noteId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  })
}

export async function deleteNote(noteId: number): Promise<void> {
  await request(`/api/notes/${noteId}`, { method: "DELETE" })
}

// ---- 学伴角色（Companion Character）----

export interface Character {  id: string
  name: string
  catchphrases: {
    correct?: string
    wrong?: string
    greeting?: string
    celebrate?: string
  }
  persona_prompt: string
  voice: { provider?: string; voice_id?: string }
  motions: string[]
  /** 各动作槽是否有素材（前端据此降级占位） */
  motion_assets: Record<string, boolean>
  has_assets: boolean
}

export async function listCharacters(): Promise<Character[]> {
  return request<Character[]>("/api/characters")
}

export async function getCharacter(id: string): Promise<Character> {
  return request<Character>(`/api/characters/${id}`)
}

/** 角色某动作的形象素材 URL */
export function getCharacterAssetUrl(characterId: string, motion: string): string {
  return `${API_BASE}/api/characters/${characterId}/assets/${motion}`
}

/** TTS：文本转语音，返回音频 Blob（MP3），音色随角色 */
export async function synthesizeSpeech(text: string, characterId?: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/characters/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, character_id: characterId ?? null }),
  })
  if (!response.ok) {
    throw new Error(`TTS 失败: HTTP ${response.status}`)
  }
  return response.blob()
}
