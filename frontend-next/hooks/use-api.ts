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
  submitQuizAnswer,
  clearQuiz,
  generateFlashcards,
  listFlashcards,
  getFlashcardStats,
  setFlashcardFamiliarity,
  clearFlashcards,
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
  type QuizGenerateResponse,
  type QuizAnswerResponse,
  type QuizScope,
  type Flashcard,
  type FlashcardGenerateResponse,
  type FlashcardStats,
  type Familiarity,
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
  return useMutation<ChatResponse, Error, { courseId: number; question: string; scope: ChatScope; courseIds?: number[] }>({
    mutationFn: ({ courseId, question, scope, courseIds }) => askQuestion(courseId, question, scope, courseIds),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["chat", variables.courseId, "history"] })
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

export function useWrongQuiz(scope: QuizScope, options?: Partial<UseQueryOptions<Question[], Error>>) {
  return useQuery<Question[], Error>({
    queryKey: [...quizKey(scope), "wrong"],
    queryFn: () => listWrongQuiz(scope),
    ...options,
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
