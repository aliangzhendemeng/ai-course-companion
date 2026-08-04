"use client"

import { useMemo, useState } from "react"
import {
  ChevronLeft,
  ChevronRight,
  Download,
  Loader2,
  PlayCircle,
  RefreshCw,
  Sparkles,
  Trash2,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  useClearFlashcards,
  useFlashcards,
  useGenerateFlashcards,
  useReviewFlashcard,
} from "@/hooks/use-api"
import { formatTimestamp } from "@/lib/timestamp"
import type { Flashcard, QuizScope } from "@/lib/api"
import { downloadExport } from "@/lib/api"

interface FlashcardPanelProps {
  scope: QuizScope
  onSeek?: (timestamp: number, courseId?: number) => void
}

// 评分档：不记得/模糊/记得 → SM-2 quality
const REVIEW_LEVELS = [
  { key: "again", label: "不记得", quality: 2, className: "border-red-500 bg-red-50 text-red-700 hover:bg-red-100 dark:bg-red-950/40 dark:text-red-300" },
  { key: "hard", label: "模糊", quality: 3, className: "border-amber-500 bg-amber-50 text-amber-700 hover:bg-amber-100 dark:bg-amber-950/40 dark:text-amber-300" },
  { key: "good", label: "记得", quality: 5, className: "border-green-500 bg-green-50 text-green-700 hover:bg-green-100 dark:bg-green-950/40 dark:text-green-300" },
] as const

/** 闪卡面板：生成、翻卡、SM-2 间隔重复评分、今日复习筛选、导出。 */
export function FlashcardPanel({ scope, onSeek }: FlashcardPanelProps) {
  const { data: cards, isLoading } = useFlashcards(scope)
  const generateMutation = useGenerateFlashcards()
  const clearMutation = useClearFlashcards()
  const reviewMutation = useReviewFlashcard()

  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [todayOnly, setTodayOnly] = useState(false) // 只看到期待复习

  const now = Date.now()
  const stats = useMemo(() => {
    const all = cards ?? []
    return {
      total: all.length,
      known: all.filter((c) => c.familiarity === "known").length,
      fuzzy: all.filter((c) => c.familiarity === "fuzzy").length,
      unknown: all.filter((c) => c.familiarity === "unknown").length,
      due: all.filter((c) => new Date(c.due_date).getTime() <= now).length,
    }
  }, [cards, now])

  const list = useMemo(() => {
    const all = cards ?? []
    const filtered = todayOnly ? all.filter((c) => new Date(c.due_date).getTime() <= now) : all
    return filtered
  }, [cards, todayOnly, now])

  const current: Flashcard | undefined = list[Math.min(index, Math.max(0, list.length - 1))]

  const goTo = (next: number) => {
    setFlipped(false)
    setIndex(next)
  }

  const handleReview = (quality: number) => {
    if (!current) return
    reviewMutation.mutate(
      { scope, flashcardId: current.id, quality },
      {
        onSuccess: () => {
          if (index < list.length - 1) goTo(index + 1)
          else setFlipped(false)
        },
      },
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-3 p-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  const all = cards ?? []
  const busy = generateMutation.isPending || clearMutation.isPending

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          {all.length > 0 ? `共 ${all.length} 张` : "还没有闪卡"}
        </p>
        <div className="flex items-center gap-2">
          {all.length > 0 && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => downloadExport("flashcards", scope, "md", "flashcards.md")}
                title="导出为 Markdown"
              >
                <Download className="mr-1 h-4 w-4" />
                导出
              </Button>
              <Button variant="ghost" size="sm" onClick={() => clearMutation.mutate(scope)} disabled={busy} title="清空当前闪卡">
                <Trash2 className="mr-1 h-4 w-4" />
                清空
              </Button>
            </>
          )}
          <Button size="sm" onClick={() => generateMutation.mutate({ scope })} disabled={busy}>
            {generateMutation.isPending ? (
              <Loader2 className="mr-1 h-4 w-4 animate-spin" />
            ) : all.length > 0 ? (
              <RefreshCw className="mr-1 h-4 w-4" />
            ) : (
              <Sparkles className="mr-1 h-4 w-4" />
            )}
            {all.length > 0 ? "再出 15 张" : "生成闪卡"}
          </Button>
        </div>
      </div>

      {generateMutation.isError && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
          生成失败：{generateMutation.error.message}
        </p>
      )}

      {all.length === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
          点击"生成闪卡"，AI 会把核心概念做成记忆卡片
        </div>
      ) : (
        <>
          {/* 统计 + 今日复习筛选 */}
          <div className="flex items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-green-600 dark:text-green-400">认识 {stats.known}</span>
              <span className="text-amber-600 dark:text-amber-400">模糊 {stats.fuzzy}</span>
              <span className="text-red-600 dark:text-red-400">不认识 {stats.unknown}</span>
            </div>
            <button
              onClick={() => { setTodayOnly(!todayOnly); setIndex(0); setFlipped(false) }}
              className={[
                "rounded-full border px-2.5 py-1 transition-colors",
                todayOnly ? "border-primary bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent",
              ].join(" ")}
            >
              今日复习（{stats.due}）
            </button>
          </div>

          {list.length === 0 ? (
            <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
              {todayOnly ? "今日没有待复习的卡片 🎉" : "太棒了！所有卡片都认识了 🎉"}
            </div>
          ) : current ? (
            <>
              {/* 卡片 */}
              <button
                onClick={() => setFlipped(!flipped)}
                className="flex min-h-[120px] flex-col items-center justify-center gap-2 rounded-xl border bg-card p-4 text-center shadow-sm transition-colors hover:bg-accent/50"
              >
                <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  {flipped ? "背面 · 点击翻回" : "正面 · 点击翻面"}
                </span>
                <p className={flipped ? "text-sm leading-relaxed text-foreground" : "text-lg font-medium leading-relaxed"}>
                  {flipped ? current.back : current.front}
                </p>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  {current.interval_days > 0 && (
                    <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                      下次复习 {current.interval_days} 天后
                    </span>
                  )}
                  {current.source_timestamp != null && (
                    <span
                      onClick={(e) => {
                        e.stopPropagation()
                        onSeek?.(current.source_timestamp!, current.source_course_id ?? undefined)
                      }}
                      className="inline-flex cursor-pointer items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    >
                      <PlayCircle className="h-3 w-3" />
                      来源 {formatTimestamp(current.source_timestamp)}
                    </span>
                  )}
                </div>
              </button>

              {/* 导航 */}
              <div className="flex items-center justify-between">
                <Button variant="outline" size="sm" onClick={() => goTo(Math.max(0, index - 1))} disabled={index === 0}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-xs text-muted-foreground">
                  {Math.min(index + 1, list.length)} / {list.length}
                </span>
                <Button variant="outline" size="sm" onClick={() => goTo(Math.min(list.length - 1, index + 1))} disabled={index >= list.length - 1}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>

              {/* SM-2 评分 */}
              <div className="grid grid-cols-3 gap-2">
                {REVIEW_LEVELS.map((lv) => (
                  <button
                    key={lv.key}
                    onClick={() => handleReview(lv.quality)}
                    disabled={reviewMutation.isPending}
                    className={["rounded-lg border px-3 py-2 text-sm font-medium transition-colors", lv.className].join(" ")}
                  >
                    {reviewMutation.isPending ? <Loader2 className="mx-auto h-4 w-4 animate-spin" /> : lv.label}
                  </button>
                ))}
              </div>
            </>
          ) : null}
        </>
      )}
    </div>
  )
}
