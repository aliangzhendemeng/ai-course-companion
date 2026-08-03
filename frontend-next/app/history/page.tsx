"use client"

import { useMemo } from "react"
import { Loader2, Inbox, Trash2, MessageSquare } from "lucide-react"
import { useRouter } from "next/navigation"

import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"
import { useChatHistoryAll, useDeleteConversation } from "@/hooks/use-api"
import { deduplicateSources, formatTimestamp } from "@/lib/timestamp"
import type { HistoryItem, Source, ChatScope } from "@/lib/api"

interface ConvGroup {
  key: string
  convId: number | null
  title: string
  courseTitle: string
  courseId: number
  scope: ChatScope
  messages: HistoryItem[]
  latest: number
}

/** 按会话分组（conversation_id），未分组的孤立消息各自成组。 */
function groupByConversation(messages: HistoryItem[]): ConvGroup[] {
  const map = new Map<string, HistoryItem[]>()
  for (const m of messages) {
    const key = m.conversation_id != null ? `c${m.conversation_id}` : `n${m.id}`
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(m)
  }
  const groups: ConvGroup[] = []
  for (const [key, msgs] of Array.from(map)) {
    const sorted = [...msgs].sort((a, b) => a.id - b.id)
    const first = sorted[0]
    const firstUser = sorted.find((m) => m.role === "user")
    groups.push({
      key,
      convId: first.conversation_id ?? null,
      title: first.conversation_title || firstUser?.content.slice(0, 24) || "未命名会话",
      courseTitle: first.course_titles?.[0] || first.course_title || "",
      courseId: first.course_id,
      scope: first.scope,
      messages: sorted,
      latest: new Date(sorted[sorted.length - 1].created_at).getTime(),
    })
  }
  return groups.sort((a, b) => b.latest - a.latest)
}

const SCOPE_LABEL: Record<ChatScope, string> = {
  course: "课程问答",
  set: "学习集",
  all: "全局搜索",
}

export default function HistoryPage() {
  const router = useRouter()
  const { data: history, isLoading } = useChatHistoryAll()
  const deleteMut = useDeleteConversation()

  const groups = useMemo(() => (history ? groupByConversation(history) : []), [history])

  return (
    <div className="container mx-auto flex h-[calc(100vh-1rem)] flex-col p-4">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">问答历史</h1>
        <p className="text-sm text-muted-foreground">共 {groups.length} 个会话</p>
      </div>

      {isLoading ? (
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <ScrollArea className="flex-1 pr-2">
          <div className="space-y-4 pb-40">
            {groups.length === 0 ? (
              <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed">
                <Inbox className="mb-2 h-8 w-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">还没有问答记录</p>
              </div>
            ) : (
              groups.map((g) => (
                <ConvCard
                  key={g.key}
                  group={g}
                  onDelete={
                    g.convId !== null
                      ? () =>
                          deleteMut.mutate({ conversationId: g.convId!, courseId: g.courseId })
                      : undefined
                  }
                  onSeek={(ts) => router.push(`/courses/${g.courseId}`)}
                />
              ))
            )}
          </div>
        </ScrollArea>
      )}
    </div>
  )
}

function ConvCard({
  group,
  onDelete,
  onSeek,
}: {
  group: ConvGroup
  onDelete?: () => void
  onSeek?: (timestamp: number, courseId?: number) => void
}) {
  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-primary" />
          <span className="font-semibold">{group.title}</span>
          <Badge variant="secondary">{SCOPE_LABEL[group.scope]}</Badge>
          {group.courseTitle && (
            <span className="text-xs text-muted-foreground">{group.courseTitle}</span>
          )}
          <span className="text-xs text-muted-foreground">
            · {group.messages.length} 条消息
          </span>
        </div>
        {onDelete && (
          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={onDelete}>
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {group.messages.map((m) => (
          <MessageRow key={m.id} message={m} onSeek={onSeek} />
        ))}
      </div>
    </div>
  )
}

function MessageRow({
  message,
  onSeek,
}: {
  message: HistoryItem
  onSeek?: (timestamp: number, courseId?: number) => void
}) {
  const isUser = message.role === "user"
  const groups = deduplicateSources(normalizeSources(message.sources))
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${
          isUser
            ? "rounded-tr-sm bg-secondary text-secondary-foreground"
            : "rounded-tl-sm border bg-background"
        }`}
      >
        <MarkdownRenderer>{message.content}</MarkdownRenderer>
        {!isUser && groups.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {groups.map((g, i) => (
              <button
                key={i}
                onClick={() => onSeek?.(g.timestamp)}
                className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground hover:bg-accent"
              >
                {g.courseTitle ? `${g.courseTitle} · ` : ""}
                {formatTimestamp(g.timestamp)}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function normalizeSources(sources: HistoryItem["sources"]): Source[] {
  if (!sources) return []
  if (Array.isArray(sources)) return sources
  if (typeof sources === "string") {
    try {
      const parsed = JSON.parse(sources)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }
  return []
}
