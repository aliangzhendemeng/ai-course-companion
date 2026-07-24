"use client"

import { useRef, useEffect, useState } from "react"
import { Send, Loader2, BookOpen, Globe } from "lucide-react"

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
import type { Source, ChatMessage } from "@/lib/api"

interface ChatPanelProps {
  courseId: number
  messages: ChatMessage[]
  isLoading?: boolean
  onSend: (question: string, scope: "course" | "all") => void
  onSeek?: (timestamp: number, courseId?: number) => void
}

export function ChatPanel({ courseId, messages, isLoading, onSend, onSeek }: ChatPanelProps) {
  const [input, setInput] = useState("")
  const [scope, setScope] = useState<"course" | "all">("course")
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const handleSend = () => {
    const question = input.trim()
    if (!question || isLoading) return
    onSend(question, scope)
    setInput("")
  }

  return (
    <div className="flex h-full flex-col rounded-xl border bg-card shadow-sm">
      <div className="flex items-center justify-between border-b p-4">
        <h3 className="font-semibold">知识问答</h3>
        <Select value={scope} onValueChange={(v) => setScope(v as "course" | "all")}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="course">
              <span className="flex items-center gap-2">
                <BookOpen className="h-4 w-4" />
                当前课程
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
            placeholder="输入你的问题..."
            className="min-h-[60px] flex-1 resize-none"
          />
          <Button
            size="icon"
            className="h-auto shrink-0"
            disabled={!input.trim() || isLoading}
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
  const sources = normalizeSources(message.sources)
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
          isUser
            ? "rounded-tr-sm bg-secondary text-secondary-foreground"
            : "rounded-tl-sm border bg-background"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {!isUser && sources.length > 0 ? (
          <div className="mt-3 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">参考来源</p>
            <div className="flex flex-wrap gap-2">
              {sources.map((source, idx) => (
                <SourceChip key={idx} source={source} onSeek={onSeek} />
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

function SourceChip({ source, onSeek }: { source: Source; onSeek?: (timestamp: number, courseId?: number) => void }) {
  const label = source.course_title && source.course_id ? `${source.course_title} · ` : ""
  const time = formatTime(source.timestamp)
  return (
    <button
      onClick={() => onSeek?.(source.timestamp, source.course_id || undefined)}
      className="max-w-[200px] truncate rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground"
      title={`${source.type} · ${time} · ${source.text}`}
    >
      {label}{time}
    </button>
  )
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, "0")}`
}
