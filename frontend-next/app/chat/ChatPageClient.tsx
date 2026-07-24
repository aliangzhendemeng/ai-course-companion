"use client"

import { useState } from "react"
import { Loader2 } from "lucide-react"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useCourses, useAskQuestion } from "@/hooks/use-api"
import { ChatPanel } from "@/components/ChatPanel"
import { useRouter } from "next/navigation"
import type { Course } from "@/lib/api"

interface ChatPageClientProps {
  initialCourses: Course[]
}

export function ChatPageClient({ initialCourses }: ChatPageClientProps) {
  const router = useRouter()
  const { data: courses, isLoading: coursesLoading } = useCourses({
    initialData: initialCourses,
    staleTime: 5000,
  })
  const [courseId, setCourseId] = useState<number | "">("")
  const [scope, setScope] = useState<"course" | "all">("all")
  const [input, setInput] = useState("")
  const askMutation = useAskQuestion()

  const completedCourses = courses?.filter((c) => c.status === "completed") || []

  const handleSend = () => {
    if (!courseId || !input.trim()) return
    askMutation.mutate({ courseId, question: input.trim(), scope })
    setInput("")
  }

  const handleSeek = (timestamp: number, targetCourseId?: number) => {
    const id = targetCourseId || courseId
    if (id) {
      router.push(`/courses/${id}?timestamp=${timestamp}`)
    }
  }

  return (
    <div className="container mx-auto flex h-[calc(100vh-1rem)] flex-col p-4">
      <div className="mb-4 flex flex-wrap items-center gap-4">
        <h1 className="text-2xl font-bold">知识问答</h1>
        <div className="flex items-center gap-2">
          {coursesLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Select
              value={courseId.toString()}
              onValueChange={(v) => setCourseId(Number(v))}
            >
              <SelectTrigger className="w-56">
                <SelectValue placeholder="选择课程" />
              </SelectTrigger>
              <SelectContent>
                {completedCourses.length === 0 ? (
                  <SelectItem value="__empty__" disabled>
                    暂无可用的已完成课程
                  </SelectItem>
                ) : (
                  completedCourses.map((c) => (
                    <SelectItem key={c.id} value={c.id.toString()}>
                      {c.title}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          )}
          <Select value={scope} onValueChange={(v) => setScope(v as "course" | "all")}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="course">当前课程</SelectItem>
              <SelectItem value="all">全部课程</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {courseId ? (
        <ChatPanel
          courseId={courseId}
          messages={askMutation.data ? buildMessages(askMutation.data, askMutation.variables) : []}
          isLoading={askMutation.isPending}
          onSend={(question, scope) => askMutation.mutate({ courseId, question, scope })}
          onSeek={handleSeek}
        />
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed text-muted-foreground">
          <p className="mb-4">选择一门课程开始提问，或切换到“全部课程”进行跨课程搜索</p>
          {coursesLoading ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : completedCourses.length === 0 ? (
            <p>暂无可用的已完成课程</p>
          ) : null}
        </div>
      )}
    </div>
  )
}

function buildMessages(
  data: { answer: string; sources: import("@/lib/api").Source[] | null },
  variables?: { question: string }
) {
  const messages: import("@/lib/api").ChatMessage[] = []
  if (variables?.question) {
    messages.push({ role: "user", content: variables.question })
  }
  messages.push({ role: "assistant", content: data.answer, sources: data.sources })
  return messages
}
