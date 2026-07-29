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
  type Course,
  type CourseDetail,
  type Summary,
  type ChatResponse,
  type ChatMessage,
  type Settings,
  type HistoryItem,
  type TranscriptDebug,
  type FrameDebug,
  type SummaryDebug,
  type ChatDebug,
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
  return useMutation<ChatResponse, Error, { courseId: number; question: string; scope: "course" | "all" }>({
    mutationFn: ({ courseId, question, scope }) => askQuestion(courseId, question, scope),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["chat", variables.courseId, "history"] })
      queryClient.invalidateQueries({ queryKey: ["history"] })
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
