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
  useSetFlashcardFamiliarity,
} from "@/hooks/use-api"
import { formatTimestamp } from "@/lib/timestamp"
import type { Familiarity, Flashcard, QuizScope } from "@/lib/api"
import { downloadExport } from "@/lib/api"

interface FlashcardPanelProps {
  scope: QuizScope
  onSeek?: (timestamp: number, courseId?: number) => void
}

const FAMILIARITY_META: Record<Familiarity, { label: string; className: string }> = {
  known: { label: "认识", className: "border-green-500 bg-green-50 text-green-700 dark:bg-green-950/40 dark:text-green-300" },
  fuzzy: { label: "模糊", className: "border-amber-500 bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300" },
  unknown: { label: "不认识", className: "border-red-500 bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300" },
}

/** 闪卡面板：生成、翻卡、三档熟悉度标记、统计、筛选。 */
export function FlashcardPanel({ scope, onSeek }: FlashcardPanelProps) {
  const { data: cards, isLoading } = useFlashcards(scope)
  const generateMutation = useGenerateFlashcards()
  const clearMutation = useClearFlashcards()
  const familiarityMutation = useSetFlashcardFamiliarity()

  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [onlyHard, setOnlyHard] = useState(false) // 只看 模糊+不认识

  const list = useMemo(() => {
    const all = cards ?? []
    return onlyHard ? all.filter((c) => c.familiarity !== "known") : all
  }, [cards, onlyHard])

  // 当前卡（索引越界时回退到 0）
  const current: Flashcard | undefined = list[Math.min(index, Math.max(0, list.length - 1))]

  const stats = useMemo(() => {
    const all = cards ?? []
    return {
      total: all.length,
      known: all.filter((c) => c.familiarity === "known").length,
      fuzzy: all.filter((c) => c.familiarity === "fuzzy").length,
      unknown: all.filter((c) => c.familiarity === "unknown").length,
    }
  }, [cards])

  const goTo = (next: number) => {
    setFlipped(false)
    setIndex(next)
  }

  const handleMark = (familiarity: Familiarity) => {
    if (!current) return
    familiarityMutation.mutate(
      { scope, flashcardId: current.id, familiarity },
      {
        onSuccess: () => {
          // 标记后自动前进到下一张
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
              <Button
                variant="ghost"
                size="sm"
                onClick={() => downloadExport("flashcards", scope, "anki", "flashcards-anki.txt")}
                title="导出为 Anki 可导入的 TSV"
              >
                Anki
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
          {/* 统计 + 筛选 */}
          <div className="flex items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-green-600 dark:text-green-400">认识 {stats.known}</span>
              <span className="text-amber-600 dark:text-amber-400">模糊 {stats.fuzzy}</span>
              <span className="text-red-600 dark:text-red-400">不认识 {stats.unknown}</span>
            </div>
            <button
              onClick={() => { setOnlyHard(!onlyHard); setIndex(0); setFlipped(false) }}
              className={[
                "rounded-full border px-2.5 py-1 transition-colors",
                onlyHard ? "border-primary bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent",
              ].join(" ")}
            >
              只看模糊+不认识
            </button>
          </div>

          {list.length === 0 ? (
            <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
              太棒了！所有卡片都认识了 🎉
            </div>
          ) : current ? (
            <>
              {/* 卡片 */}
              <button
                onClick={() => setFlipped(!flipped)}
                className="flex min-h-[220px] flex-1 flex-col items-center justify-center gap-3 rounded-xl border bg-card p-6 text-center shadow-sm transition-colors hover:bg-accent/50"
              >
                <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  {flipped ? "背面 · 点击翻回" : "正面 · 点击翻面"}
                </span>
                <p className={flipped ? "text-sm leading-relaxed text-foreground" : "text-lg font-medium leading-relaxed"}>
                  {flipped ? current.back : current.front}
                </p>
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
              </button>

              {/* 导航 + 标记 */}
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

              <div className="grid grid-cols-3 gap-2">
                {(Object.keys(FAMILIARITY_META) as Familiarity[]).map((level) => (
                  <button
                    key={level}
                    onClick={() => handleMark(level)}
                    disabled={familiarityMutation.isPending}
                    className={[
                      "rounded-lg border px-3 py-2 text-sm transition-colors",
                      current.familiarity === level
                        ? FAMILIARITY_META[level].className
                        : "text-muted-foreground hover:bg-accent",
                    ].join(" ")}
                  >
                    {familiarityMutation.isPending ? <Loader2 className="mx-auto h-4 w-4 animate-spin" /> : FAMILIARITY_META[level].label}
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
