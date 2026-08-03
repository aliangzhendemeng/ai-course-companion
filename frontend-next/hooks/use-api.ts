// TanStack Query hooks。

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query"

import {
  listCourses,
  getCourse,
  uploadCourse,
  deleteCourse,
  reprocessCourse,
  getSummary,
  askQuestion,
  getChatHistory,
  getSettings,
  saveSettings,
  listChatHistory,
  deleteChatHistory,
  getCourseTranscriptsDebug,
  getCourseFramesDebug,
  getCourseSummaryDebug,
  getChatDebug,
  listStudySets,
  createStudySet,
  updateStudySet,
  deleteStudySet,
  generateQuiz,
  listQuiz,
  listWrongQuiz,
  clearWrongQuiz,
  submitQuizAnswer,
  clearQuiz,
  generateFlashcards,
  listFlashcards,
  getFlashcardStats,
  setFlashcardFamiliarity,
  clearFlashcards,
  listCharacters,
  getStudyStats,
  getDashboard,
  summarizeSegment,
  getChapters,
  listConversations,
  getConversationMessages,
  renameConversation,
  deleteConversation,
  listNotes,
  createNote,
  updateNote,
  deleteNote,
  type Course,
  type CourseDetail,
  type Summary,
  type ChatResponse,
  type ChatMessage,
  type ChatScope,
  type Settings,
  type HistoryItem,
  type TranscriptDebug,
  type FrameDebug,
  type SummaryDebug,
  type ChatDebug,
  type StudySet,
  type Question,
  type WrongQuestion,
  type QuizGenerateResponse,
  type QuizAnswerResponse,
  type QuizScope,
  type Flashcard,
  type FlashcardGenerateResponse,
  type FlashcardStats,
  type Familiarity,
  type Character,
  type Note,
  type NoteKind,
  type StudyStats,
  type Dashboard,
  type SegmentSummary,
  type Chapter,
  type Conversation,
} from "@/lib/api"

export function useCourses(options?: Partial<UseQueryOptions<Course[], Error>>) {
  return useQuery<Course[], Error>({
    queryKey: ["courses"],
    queryFn: listCourses,
    refetchInterval: 2000,
    staleTime: 5000,
    ...options,
  })
}

export function useCourse(id: number, options?: Partial<UseQueryOptions<CourseDetail, Error>>) {
  return useQuery<CourseDetail, Error>({
    queryKey: ["courses", id],
    queryFn: () => getCourse(id),
    refetchInterval: 5000,
    ...options,
  })
}

export function useSummary(courseId: number, options?: Partial<UseQueryOptions<Summary, Error>>) {
  return useQuery<Summary, Error>({
    queryKey: ["summaries", courseId],
    queryFn: () => getSummary(courseId),
    ...options,
  })
}

export function useChatHistory(courseId: number, options?: Partial<UseQueryOptions<ChatMessage[], Error>>) {
  return useQuery<ChatMessage[], Error>({
    queryKey: ["chat", courseId, "history"],
    queryFn: () => getChatHistory(courseId),
    ...options,
  })
}

export function useUploadCourse() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: uploadCourse,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses"] })
    },
  })
}

export function useDeleteCourse() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteCourse,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses"] })
    },
  })
}

export function useReprocessCourse() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: reprocessCourse,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["courses", id] })
      queryClient.invalidateQueries({ queryKey: ["courses"] })
    },
  })
}

export function useAskQuestion() {
  const queryClient = useQueryClient()
  return useMutation<ChatResponse, Error, { courseId: number; question: string; scope: ChatScope; courseIds?: number[]; image?: string; conversationId?: number }>({
    mutationFn: ({ courseId, question, scope, courseIds, image, conversationId }) => askQuestion(courseId, question, scope, courseIds, image, conversationId),
    onSuccess: (data, variables) => {
      // 失效当前会话消息 + 该课程会话列表 + 全局历史
      if (data.conversation_id) {
        queryClient.invalidateQueries({ queryKey: ["conversation", data.conversation_id] })
      }
      queryClient.invalidateQueries({ queryKey: ["conversations", variables.courseId] })
      queryClient.invalidateQueries({ queryKey: ["chat", variables.courseId, "history"] })
      queryClient.invalidateQueries({ queryKey: ["history"] })
    },
  })
}

// ---- 会话（Conversation）----

export function useConversations(courseId: number) {
  return useQuery<Conversation[], Error>({
    queryKey: ["conversations", courseId],
    queryFn: () => listConversations(courseId),
    staleTime: 30 * 1000,
  })
}

export function useConversationMessages(conversationId: number | null) {
  return useQuery<ChatMessage[], Error>({
    queryKey: ["conversation", conversationId],
    queryFn: () => getConversationMessages(conversationId as number),
    enabled: conversationId !== null,
  })
}

export function useRenameConversation() {
  const queryClient = useQueryClient()
  return useMutation<Conversation, Error, { conversationId: number; courseId: number; title: string }>({
    mutationFn: ({ conversationId, title }) => renameConversation(conversationId, title),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["conversations", variables.courseId] })
    },
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, { conversationId: number; courseId: number }>({
    mutationFn: ({ conversationId }) => deleteConversation(conversationId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["conversations", variables.courseId] })
      queryClient.invalidateQueries({ queryKey: ["history"] })
    },
  })
}

// ---- 学习集 ----

export function useStudySets(options?: Partial<UseQueryOptions<StudySet[], Error>>) {
  return useQuery<StudySet[], Error>({
    queryKey: ["study-sets"],
    queryFn: listStudySets,
    staleTime: 1000,
    ...options,
  })
}

export function useCreateStudySet() {
  const queryClient = useQueryClient()
  return useMutation<StudySet, Error, { name: string; courseIds: number[] }>({
    mutationFn: ({ name, courseIds }) => createStudySet(name, courseIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["study-sets"] })
    },
  })
}

export function useUpdateStudySet() {
  const queryClient = useQueryClient()
  return useMutation<StudySet, Error, { id: number; name?: string; course_ids?: number[] }>({
    mutationFn: ({ id, ...payload }) => updateStudySet(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["study-sets"] })
    },
  })
}

export function useDeleteStudySet() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, number>({
    mutationFn: deleteStudySet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["study-sets"] })
    },
  })
}

// ---- 测验 ----

function quizKey(scope: QuizScope) {
  return scope.studySetId != null ? ["quiz", "set", scope.studySetId] : ["quiz", "course", scope.courseId]
}

export function useQuiz(scope: QuizScope, options?: Partial<UseQueryOptions<Question[], Error>>) {
  return useQuery<Question[], Error>({
    queryKey: quizKey(scope),
    queryFn: () => listQuiz(scope),
    ...options,
  })
}

export function useWrongQuiz(scope: QuizScope, options?: Partial<UseQueryOptions<WrongQuestion[], Error>>) {
  return useQuery<WrongQuestion[], Error>({
    queryKey: [...quizKey(scope), "wrong"],
    queryFn: () => listWrongQuiz(scope),
    ...options,
  })
}

export function useClearWrongQuiz() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, QuizScope>({
    mutationFn: (scope) => clearWrongQuiz(scope),
    onSuccess: (_, scope) => {
      queryClient.invalidateQueries({ queryKey: [...quizKey(scope), "wrong"] })
      // 清错题本删了作答记录，题目 Tab 的作答进度也要刷新
      queryClient.invalidateQueries({ queryKey: quizKey(scope) })
    },
  })
}

export function useGenerateQuiz() {
  const queryClient = useQueryClient()
  return useMutation<QuizGenerateResponse, Error, { scope: QuizScope; count?: number }>({
    mutationFn: ({ scope, count }) => generateQuiz(scope, count),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: quizKey(variables.scope) })
    },
  })
}

export function useSubmitQuizAnswer() {
  const queryClient = useQueryClient()
  return useMutation<QuizAnswerResponse, Error, { questionId: number; answer: string; scope?: QuizScope }>({
    mutationFn: ({ questionId, answer }) => submitQuizAnswer(questionId, answer),
    onSuccess: (_, variables) => {
      if (variables.scope) {
        // 作答影响错题本，刷新它
        queryClient.invalidateQueries({ queryKey: [...quizKey(variables.scope), "wrong"] })
      }
    },
  })
}

export function useClearQuiz() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, QuizScope>({
    mutationFn: (scope) => clearQuiz(scope),
    onSuccess: (_, scope) => {
      queryClient.invalidateQueries({ queryKey: quizKey(scope) })
    },
  })
}

// ---- 闪卡 ----

function flashcardKey(scope: QuizScope) {
  return scope.studySetId != null ? ["flashcards", "set", scope.studySetId] : ["flashcards", "course", scope.courseId]
}

export function useFlashcards(scope: QuizScope, options?: Partial<UseQueryOptions<Flashcard[], Error>>) {
  return useQuery<Flashcard[], Error>({
    queryKey: flashcardKey(scope),
    queryFn: () => listFlashcards(scope),
    ...options,
  })
}

export function useFlashcardStats(scope: QuizScope, options?: Partial<UseQueryOptions<FlashcardStats, Error>>) {
  return useQuery<FlashcardStats, Error>({
    queryKey: [...flashcardKey(scope), "stats"],
    queryFn: () => getFlashcardStats(scope),
    ...options,
  })
}

export function useGenerateFlashcards() {
  const queryClient = useQueryClient()
  return useMutation<FlashcardGenerateResponse, Error, { scope: QuizScope; count?: number }>({
    mutationFn: ({ scope, count }) => generateFlashcards(scope, count),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: flashcardKey(variables.scope) })
    },
  })
}

export function useSetFlashcardFamiliarity() {
  const queryClient = useQueryClient()
  return useMutation<Flashcard, Error, { scope: QuizScope; flashcardId: number; familiarity: Familiarity }>({
    mutationFn: ({ flashcardId, familiarity }) => setFlashcardFamiliarity(flashcardId, familiarity),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: flashcardKey(variables.scope) })
    },
  })
}

export function useClearFlashcards() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, QuizScope>({
    mutationFn: (scope) => clearFlashcards(scope),
    onSuccess: (_, scope) => {
      queryClient.invalidateQueries({ queryKey: flashcardKey(scope) })
    },
  })
}

// ---- 笔记/书签 ----

function noteKey(courseId: number) {
  return ["notes", "course", courseId]
}

export function useNotes(courseId: number, options?: Partial<UseQueryOptions<Note[], Error>>) {
  return useQuery<Note[], Error>({
    queryKey: noteKey(courseId),
    queryFn: () => listNotes(courseId),
    ...options,
  })
}

export function useCreateNote() {
  const queryClient = useQueryClient()
  return useMutation<Note, Error, { course_id: number; kind: NoteKind; content?: string; timestamp: number }>({
    mutationFn: (payload) => createNote(payload),
    onSuccess: (note) => {
      queryClient.invalidateQueries({ queryKey: noteKey(note.course_id) })
    },
  })
}

export function useUpdateNote() {
  const queryClient = useQueryClient()
  return useMutation<Note, Error, { noteId: number; courseId: number; content: string }>({
    mutationFn: ({ noteId, content }) => updateNote(noteId, content),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: noteKey(variables.courseId) })
    },
  })
}

export function useDeleteNote() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, { noteId: number; courseId: number }, { prev: Note[] | undefined }>({
    mutationFn: ({ noteId }) => deleteNote(noteId),
    // 乐观更新：点击立即从列表移除，避免"删了还在"的错觉
    onMutate: async ({ noteId, courseId }) => {
      await queryClient.cancelQueries({ queryKey: noteKey(courseId) })
      const prev = queryClient.getQueryData<Note[]>(noteKey(courseId))
      queryClient.setQueryData<Note[]>(noteKey(courseId), (old) =>
        (old ?? []).filter((n) => n.id !== noteId)
      )
      return { prev }
    },
    onError: (_err, { courseId }, context) => {
      // 失败回滚
      if (context?.prev) queryClient.setQueryData(noteKey(courseId), context.prev)
    },
    onSettled: (_data, _err, { courseId }) => {
      queryClient.invalidateQueries({ queryKey: noteKey(courseId) })
    },
  })
}

// ---- 学伴角色 ----

export function useCharacters(options?: Partial<UseQueryOptions<Character[], Error>>) {
  return useQuery<Character[], Error>({
    queryKey: ["characters"],
    queryFn: listCharacters,
    staleTime: 60000,
    ...options,
  })
}

export function useSettings(options?: Partial<UseQueryOptions<Settings, Error>>) {
  return useQuery<Settings, Error>({
    queryKey: ["settings"],
    queryFn: getSettings,
    staleTime: 1000,
    ...options,
  })
}

export function useSaveSettings() {
  const queryClient = useQueryClient()
  return useMutation<Settings, Error, Partial<Settings>>({
    mutationFn: saveSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] })
    },
  })
}

export function useChatHistoryAll(options?: Partial<UseQueryOptions<HistoryItem[], Error>>) {
  return useQuery<HistoryItem[], Error>({
    queryKey: ["history"],
    queryFn: listChatHistory,
    staleTime: 1000,
    ...options,
  })
}

export function useDeleteChatHistory() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, number>({
    mutationFn: deleteChatHistory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["history"] })
    },
  })
}

export function useCourseTranscriptsDebug(courseId: number, options?: Partial<UseQueryOptions<TranscriptDebug[], Error>>) {
  return useQuery<TranscriptDebug[], Error>({
    queryKey: ["debug", courseId, "transcripts"],
    queryFn: () => getCourseTranscriptsDebug(courseId),
    ...options,
  })
}

export function useCourseFramesDebug(courseId: number, options?: Partial<UseQueryOptions<FrameDebug[], Error>>) {
  return useQuery<FrameDebug[], Error>({
    queryKey: ["debug", courseId, "frames"],
    queryFn: () => getCourseFramesDebug(courseId),
    ...options,
  })
}

export function useCourseSummaryDebug(courseId: number, options?: Partial<UseQueryOptions<SummaryDebug, Error>>) {
  return useQuery<SummaryDebug, Error>({
    queryKey: ["debug", courseId, "summary"],
    queryFn: () => getCourseSummaryDebug(courseId),
    ...options,
  })
}

export function useChatDebug(messageId: number | null, options?: Partial<UseQueryOptions<ChatDebug, Error>>) {
  return useQuery<ChatDebug, Error>({
    queryKey: ["debug", "chat", messageId],
    queryFn: () => getChatDebug(messageId as number),
    enabled: messageId !== null,
    ...options,
  })
}

// ---- 学习打卡统计 ----

export function useStudyStats() {
  return useQuery<StudyStats, Error>({
    queryKey: ["study-stats"],
    queryFn: () => getStudyStats(),
    // 学习行为发生后刷新（5 分钟也兜底一次）
    refetchOnWindowFocus: true,
    staleTime: 60 * 1000,
  })
}

// ---- 掌握度仪表盘 ----

export function useDashboard() {
  return useQuery<Dashboard, Error>({
    queryKey: ["dashboard"],
    queryFn: () => getDashboard(),
    staleTime: 60 * 1000,
  })
}

// ---- 时间段总结 ----

export function useSummarizeSegment() {
  return useMutation<SegmentSummary, Error, { courseId: number; start: number; end: number }>({
    mutationFn: ({ courseId, start, end }) => summarizeSegment(courseId, start, end),
  })
}

// ---- 本章节速览 ----

export function useChapters(courseId: number) {
  return useQuery<Chapter[], Error>({
    queryKey: ["chapters", courseId],
    queryFn: () => getChapters(courseId),
    staleTime: 5 * 60 * 1000,
  })
}
