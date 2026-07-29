"use client"

import { useRef, useEffect, useState } from "react"
import { Send, Loader2, BookOpen, Globe, Layers } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"
import { StudySetPicker } from "@/components/StudySetPicker"
import { deduplicateSources, formatTimestamp } from "@/lib/timestamp"
import type { Source, ChatMessage, ChatScope } from "@/lib/api"

interface ChatPanelProps {
  courseId: number
  messages: ChatMessage[]
  isLoading?: boolean
  onSend: (question: string, scope: ChatScope, courseIds?: number[]) => void
  onSeek?: (timestamp: number, courseId?: number) => void
  defaultScope?: ChatScope
  lockScope?: boolean
  /** 隐藏"当前课程"选项（用于跨课程的全局搜索页） */
  hideCourseScope?: boolean
  title?: string
}

export function ChatPanel({
  courseId,
  messages,
  isLoading,
  onSend,
  onSeek,
  defaultScope = "course",
  lockScope = false,
  hideCourseScope = false,
  title = "知识问答",
}: ChatPanelProps) {
  const [input, setInput] = useState("")
  const [scope, setScope] = useState<ChatScope>(defaultScope)
  // 学习集模式：选中的课程 id 集合
  const [setCourseIds, setSetCourseIds] = useState<number[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const handleSend = () => {
    const question = input.trim()
    if (!question || isLoading) return
    onSend(question, scope, scope === "set" ? setCourseIds : undefined)
    setInput("")
  }

  const handleScopeChange = (v: string) => {
    if (v === "set") {
      // 进入学习集模式；尚未选课时先不切换，由 Picker 应用后再切
      setScope("set")
    } else {
      setScope(v as ChatScope)
    }
  }

  const canSend = scope === "set" ? setCourseIds.length > 0 : true

  return (
    <div className="flex h-full flex-col rounded-xl border bg-card shadow-sm">
      <div className="flex items-center justify-between gap-2 border-b p-4">
        <h3 className="font-semibold">{title}</h3>
        {lockScope ? (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Globe className="h-3.5 w-3.5" />
            全部课程
          </span>
        ) : (
          <div className="flex items-center gap-2">
            <Select value={scope} onValueChange={handleScopeChange}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {!hideCourseScope && (
                  <SelectItem value="course">
                    <span className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4" />
                      当前课程
                    </span>
                  </SelectItem>
                )}
                <SelectItem value="set">
                  <span className="flex items-center gap-2">
                    <Layers className="h-4 w-4" />
                    选择课程
                  </span>
                </SelectItem>
                <SelectItem value="all">
                  <span className="flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    全部课程
                  </span>
                </SelectItem>
              </SelectContent>
            </Select>

            {scope === "set" && (
              <StudySetPicker
                selectedCourseIds={setCourseIds}
                onApply={(ids) => setSetCourseIds(ids)}
                trigger={
                  <Button variant="outline" size="sm" className="h-9">
                    <Layers className="mr-1 h-4 w-4" />
                    {setCourseIds.length > 0 ? `已选 ${setCourseIds.length} 门` : "选择课程"}
                  </Button>
                }
              />
            )}
          </div>
        )}
      </div>

      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} onSeek={onSeek} />
          ))}
          {isLoading ? (
            <div className="flex gap-1">
              <span className="h-2 w-2 animate-pulse-dot rounded-full bg-primary [animation-delay:-0.3s]" />
              <span className="h-2 w-2 animate-pulse-dot rounded-full bg-primary [animation-delay:-0.15s]" />
              <span className="h-2 w-2 animate-pulse-dot rounded-full bg-primary" />
            </div>
          ) : null}
        </div>
      </ScrollArea>

      <div className="border-t p-4">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder={
              scope === "set" && setCourseIds.length === 0
                ? "请先在上方选择要一起学习的课程..."
                : "输入你的问题..."
            }
            className="min-h-[60px] flex-1 resize-none"
          />
          <Button
            size="icon"
            className="h-auto shrink-0"
            disabled={!input.trim() || isLoading || !canSend}
            onClick={handleSend}
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({
  message,
  onSeek,
}: {
  message: ChatMessage
  onSeek?: (timestamp: number, courseId?: number) => void
}) {
  const isUser = message.role === "user"
  const groups = deduplicateSources(normalizeSources(message.sources))
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
          isUser
            ? "rounded-tr-sm bg-secondary text-secondary-foreground"
            : "rounded-tl-sm border bg-background"
        }`}
      >
        <MarkdownRenderer>{message.content}</MarkdownRenderer>
        {!isUser && groups.length > 0 ? (
          <div className="mt-3 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">参考来源</p>
            <div className="flex flex-wrap gap-2">
              {groups.map((group, idx) => (
                <SourceChip key={idx} group={group} onSeek={onSeek} />
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}

function normalizeSources(sources: ChatMessage["sources"]): Source[] {
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

function SourceChip({
  group,
  onSeek,
}: {
  group: import("@/lib/timestamp").DeduplicatedSource
  onSeek?: (timestamp: number, courseId?: number) => void
}) {
  const first = group.sources[0]
  const label = group.courseTitle ? `${group.courseTitle} · ` : ""
  const count = group.sources.length
  const time = formatTimestamp(group.timestamp)
  return (
    <button
      onClick={() => onSeek?.(group.timestamp, first.course_id || undefined)}
      className="max-w-[220px] truncate rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground"
      title={`${first.type} · ${time} · ${first.text}`}
    >
      {label}{time}
      {count > 1 && <span className="ml-1 text-[10px] opacity-80">({count} 个来源)</span>}
    </button>
  )
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, "0")}`
}
