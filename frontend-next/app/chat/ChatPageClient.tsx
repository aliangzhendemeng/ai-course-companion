"use client"

import { Loader2, Globe } from "lucide-react"

import { useCourses, useAskQuestion } from "@/hooks/use-api"
import { ChatPanel } from "@/components/ChatPanel"
import { useRouter } from "next/navigation"
import type { Course, ChatMessage, Source } from "@/lib/api"

interface ChatPageClientProps {
  initialCourses: Course[]
}

export function ChatPageClient({ initialCourses }: ChatPageClientProps) {
  const router = useRouter()
  const { data: courses, isLoading: coursesLoading } = useCourses({
    initialData: initialCourses,
    staleTime: 5000,
  })
  const askMutation = useAskQuestion()

  const completedCourses = courses?.filter((c) => c.status === "completed") || []
  // 全局搜索无需选课；用第一个已完成课程作为问答记录的归档锚点
  const anchorCourseId = completedCourses[0]?.id

  const handleSeek = (timestamp: number, targetCourseId?: number) => {
    const id = targetCourseId || anchorCourseId
    if (id) {
      router.push(`/courses/${id}?timestamp=${timestamp}`)
    }
  }

  return (
    <div className="container mx-auto flex h-[calc(100vh-1rem)] flex-col p-4">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">全局搜索</h1>
          <p className="flex items-center gap-1 text-sm text-muted-foreground">
            <Globe className="h-3.5 w-3.5" />
            跨所有课程检索答案，结果会标注来源课程与时间点
          </p>
        </div>
        <span className="rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground">
          {coursesLoading ? "加载中…" : `共 ${completedCourses.length} 门课程`}
        </span>
      </div>

      {anchorCourseId ? (
        <ChatPanel
          courseId={anchorCourseId}
          messages={
            askMutation.data
              ? buildMessages(askMutation.data, askMutation.variables)
              : []
          }
          isLoading={askMutation.isPending}
          onSend={(question) =>
            askMutation.mutate({ courseId: anchorCourseId, question, scope: "all" })
          }
          onSeek={handleSeek}
          defaultScope="all"
          lockScope
          title="全局搜索"
        />
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed text-muted-foreground">
          {coursesLoading ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : (
            <p>还没有已完成的课程，无法进行全局搜索</p>
          )}
        </div>
      )}
    </div>
  )
}

function buildMessages(
  data: { answer: string; sources: Source[] | null },
  variables?: { question: string }
): ChatMessage[] {
  const messages: ChatMessage[] = []
  if (variables?.question) {
    messages.push({ role: "user", content: variables.question })
  }
  messages.push({ role: "assistant", content: data.answer, sources: data.sources })
  return messages
}
