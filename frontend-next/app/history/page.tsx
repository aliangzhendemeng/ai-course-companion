"use client"

import { Loader2, Inbox } from "lucide-react"
import { useRouter } from "next/navigation"

import { ScrollArea } from "@/components/ui/scroll-area"
import { HistoryCard, type QAPair } from "@/components/HistoryCard"
import { useChatHistoryAll, useDeleteChatHistory } from "@/hooks/use-api"
import type { HistoryItem } from "@/lib/api"

/** 把按时间倒序的消息列表配对成 Q&A（用户问题 + 助手回答）。
 *
 * 必须先按"对话上下文"（同一课程/同一组课程）分组再配对：
 * 不同课程的问答在时间上交错，若全局混排，一门课的 user 后面紧跟的可能是
 * 另一门课的消息，导致 user 找不到自己的 assistant，误显示"无回答记录"。
 */
function contextKey(m: HistoryItem): string {
  // set/all 用实际涉及的课程集合做 key；course 用锚点课程 id
  if (m.course_ids && m.course_ids.length > 0) {
    return "set:" + [...m.course_ids].sort((a, b) => a - b).join(",")
  }
  return `course:${m.course_id}`
}

function pairMessages(messages: HistoryItem[]): QAPair[] {
  // 1) 按对话上下文分组（保持各组内时间升序）
  const groups = new Map<string, HistoryItem[]>()
  const asc = [...messages].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  )
  for (const m of asc) {
    const key = contextKey(m)
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(m)
  }

  // 2) 各组内把 user 与紧随的 assistant 配对
  const pairs: QAPair[] = []
  for (const msgs of Array.from(groups.values())) {
    for (let i = 0; i < msgs.length; i++) {
      const cur = msgs[i]
      const next = msgs[i + 1]
      if (cur.role === "user" && next && next.role === "assistant") {
        pairs.push({ question: cur, answer: next })
        i++
      } else if (cur.role === "assistant") {
        pairs.push({ answer: cur })
      } else {
        pairs.push({ question: cur })
      }
    }
  }

  // 3) 按时间倒序，最新在最上（用每组回答/问题的时间）
  const timeOf = (p: QAPair) =>
    new Date((p.answer ?? p.question)!.created_at).getTime()
  return pairs.sort((a, b) => timeOf(b) - timeOf(a))
}

export default function HistoryPage() {
  const router = useRouter()
  const { data: history, isLoading } = useChatHistoryAll()
  const deleteMutation = useDeleteChatHistory()

  const pairs = history ? pairMessages(history) : []

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handleDebug = (id: number) => {
    const item = history?.find((h) => h.id === id)
    if (item?.course_id) {
      router.push(`/courses/${item.course_id}/debug?message=${id}`)
    }
  }

  return (
    <div className="container mx-auto flex h-[calc(100vh-1rem)] flex-col p-4">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">问答历史</h1>
        <p className="text-sm text-muted-foreground">共 {pairs.length} 组问答</p>
      </div>

      {isLoading ? (
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <ScrollArea className="flex-1 pr-2">
          <div className="space-y-4 pb-4">
            {pairs.length > 0 ? (
              pairs.map((pair, idx) => {
                const key =
                  (pair.question?.id ?? "q") + "-" + (pair.answer?.id ?? "a") + "-" + idx
                return (
                  <HistoryCard
                    key={key}
                    pair={pair}
                    onDelete={handleDelete}
                    onDebug={pair.answer ? handleDebug : undefined}
                  />
                )
              })
            ) : (
              <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed">
                <Inbox className="mb-2 h-8 w-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">还没有问答记录</p>
              </div>
            )}
          </div>
        </ScrollArea>
      )}
    </div>
  )
}
