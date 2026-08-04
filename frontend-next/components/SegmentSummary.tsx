"use client"

import { useState } from "react"
import { Clock, Loader2, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { MarkdownRenderer } from "@/components/MarkdownRenderer"
import { useSummarizeSegment } from "@/hooks/use-api"
import { useCompanion } from "@/components/companion/CompanionContext"

interface SegmentSummaryProps {
  courseId: number
  getCurrentTime: () => number
}

const WINDOWS = [2, 3, 5] as const

function fmt(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds))
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${sec.toString().padStart(2, "0")}`
}

/** 时间段总结：取视频当前时间前后 N 分钟，AI 总结这段内容。 */
export function SegmentSummary({ courseId, getCurrentTime }: SegmentSummaryProps) {
  const [window, setWindow] = useState<number>(3)
  const mutation = useSummarizeSegment()
  const { react } = useCompanion()

  const handleSummarize = () => {
    const center = getCurrentTime()
    const start = Math.max(0, center - window * 60)
    const end = center + window * 60
    react("loading")
    mutation.mutate(
      { courseId, start, end },
      {
        onSuccess: () => react("happy", undefined, false),
        onError: () => react("confused"),
      }
    )
  }

  const center = getCurrentTime()
  const start = Math.max(0, center - window * 60)
  const end = center + window * 60

  return (
    <div className="rounded-xl border bg-card p-3 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="flex items-center gap-1 text-sm font-medium">
          <Clock className="h-4 w-4 text-primary" />
          时间段总结
        </span>
        <span className="text-xs text-muted-foreground">当前 {fmt(center)}</span>
        <div className="flex items-center gap-1">
          {WINDOWS.map((w) => (
            <button
              key={w}
              onClick={() => setWindow(w)}
              className={`rounded px-2 py-0.5 text-xs ${
                window === w ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
              }`}
            >
              前后{w}分
            </button>
          ))}
        </div>
        <span className="text-xs text-muted-foreground">
          ({fmt(start)} – {fmt(end)})
        </span>
        <Button size="sm" onClick={handleSummarize} disabled={mutation.isPending} className="ml-auto">
          {mutation.isPending ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Sparkles className="mr-1 h-4 w-4" />}
          总结这段时间
        </Button>
      </div>

      {mutation.data && (
        <div className="mt-3 border-t pt-3 text-sm">
          <MarkdownRenderer>{mutation.data.summary}</MarkdownRenderer>
        </div>
      )}
      {mutation.isError && (
        <p className="mt-2 text-xs text-destructive">总结失败：{mutation.error?.message}</p>
      )}
    </div>
  )
}
