"use client"

import { PlayCircle } from "lucide-react"

import { Skeleton } from "@/components/ui/skeleton"
import { useChapters } from "@/hooks/use-api"
import { formatTimestamp } from "@/lib/timestamp"

interface ChaptersPanelProps {
  courseId: number
  onSeek?: (timestamp: number, courseId?: number) => void
}

/** 本章节速览：自动分章 + 每章标题/速览，点击跳转视频对应位置。 */
export function ChaptersPanel({ courseId, onSeek }: ChaptersPanelProps) {
  const { data: chapters, isLoading } = useChapters(courseId)
  const list = chapters ?? []

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    )
  }
  if (list.length === 0) {
    return <p className="py-6 text-center text-sm text-muted-foreground">暂无字幕，无法生成章节</p>
  }
  return (
    <ol className="space-y-2">
      {list.map((c) => (
        <li key={c.id}>
          <button
            onClick={() => onSeek?.(c.start_time)}
            className="flex w-full items-start gap-3 rounded-lg border border-transparent p-2 text-left hover:border-border hover:bg-accent"
          >
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
              {c.index}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-medium">{c.title}</span>
                <span className="flex shrink-0 items-center gap-0.5 text-xs text-muted-foreground">
                  <PlayCircle className="h-3 w-3" />
                  {formatTimestamp(c.start_time)}
                </span>
              </div>
              {c.summary && (
                <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{c.summary}</p>
              )}
            </div>
          </button>
        </li>
      ))}
    </ol>
  )
}
