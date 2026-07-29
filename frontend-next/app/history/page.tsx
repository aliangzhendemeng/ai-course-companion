"use client"

import { Loader2, Inbox } from "lucide-react"
import { useRouter } from "next/navigation"

import { ScrollArea } from "@/components/ui/scroll-area"
import { HistoryCard, type QAPair } from "@/components/HistoryCard"
import { useChatHistoryAll, useDeleteChatHistory } from "@/hooks/use-api"
import type { HistoryItem } from "@/lib/api"

/** 把按时间倒序的消息列表配对成 Q&A（用户问题 + 助手回答）。 */
function pairMessages(messages: HistoryItem[]): QAPair[] {
  // 升序处理，便于把 user 和紧随其后的 assistant 配对
  const asc = [...messages].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  )
  const pairs: QAPair[] = []
  for (let i = 0; i < asc.length; i++) {
    const cur = asc[i]
    const next = asc[i + 1]
    if (cur.role === "user" && next && next.role === "assistant") {
      pairs.push({ question: cur, answer: next })
      i++
    } else if (cur.role === "assistant") {
      // 孤立回答（找不到对应问题）
      pairs.push({ answer: cur })
    } else {
      // 孤立问题（没有回答）
      pairs.push({ question: cur })
    }
  }
  // 再倒序，最新的在最上面
  return pairs.reverse()
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
