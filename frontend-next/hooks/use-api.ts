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
  type Course,
  type CourseDetail,
  type Summary,
  type ChatResponse,
  type ChatMessage,
} from "@/lib/api"

export function useCourses(options?: Partial<UseQueryOptions<Course[], Error>>) {
  return useQuery<Course[], Error>({
    queryKey: ["courses"],
    queryFn: listCourses,
    refetchInterval: 5000,
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
    },
  })
}
