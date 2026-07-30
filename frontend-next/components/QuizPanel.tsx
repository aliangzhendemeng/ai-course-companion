"use client"

import { useState } from "react"
import { BookX, CheckCircle2, Loader2, PlayCircle, RefreshCw, Sparkles, Trash2, XCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  useClearQuiz,
  useGenerateQuiz,
  useQuiz,
  useSubmitQuizAnswer,
  useWrongQuiz,
} from "@/hooks/use-api"
import { formatTimestamp } from "@/lib/timestamp"
import type { Question, QuizScope } from "@/lib/api"

interface QuizPanelProps {
  scope: QuizScope
  onSeek?: (timestamp: number, courseId?: number) => void
}

/** 测验面板：生成、作答、判分、解析、来源跳转、错题本。 */
export function QuizPanel({ scope, onSeek }: QuizPanelProps) {
  const { data: questions, isLoading } = useQuiz(scope)
  const { data: wrongQuestions } = useWrongQuiz(scope)
  const generateMutation = useGenerateQuiz()
  const clearMutation = useClearQuiz()

  const handleGenerate = () => generateMutation.mutate({ scope })
  const handleClear = () => clearMutation.mutate(scope)

  if (isLoading) {
    return (
      <div className="space-y-3 p-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  const list = questions ?? []
  const wrong = wrongQuestions ?? []
  const busy = generateMutation.isPending || clearMutation.isPending

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          {list.length > 0 ? `共 ${list.length} 题` : "还没有测验题"}
        </p>
        <div className="flex items-center gap-2">
          {list.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
              disabled={busy}
              title="清空当前题目"
            >
              <Trash2 className="mr-1 h-4 w-4" />
              清空
            </Button>
          )}
          <Button size="sm" onClick={handleGenerate} disabled={busy}>
            {generateMutation.isPending ? (
              <Loader2 className="mr-1 h-4 w-4 animate-spin" />
            ) : list.length > 0 ? (
              <RefreshCw className="mr-1 h-4 w-4" />
            ) : (
              <Sparkles className="mr-1 h-4 w-4" />
            )}
            {list.length > 0 ? "再出 12 题" : "生成测验"}
          </Button>
        </div>
      </div>

      {generateMutation.isError && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
          出题失败：{generateMutation.error.message}
        </p>
      )}

      {list.length === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
          点击"生成测验"，AI 会根据课程内容出选择题和判断题
        </div>
      ) : (
        <Tabs defaultValue="all" className="flex min-h-0 flex-1 flex-col">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="all">题目（{list.length}）</TabsTrigger>
            <TabsTrigger value="wrong" className="gap-1">
              <BookX className="h-3.5 w-3.5" />
              错题本（{wrong.length}）
            </TabsTrigger>
          </TabsList>
          <TabsContent value="all" className="mt-3 min-h-0 flex-1">
            <ScrollArea className="h-full">
              <ol className="space-y-4 pr-3">
                {list.map((q, idx) => (
                  <QuestionCard key={q.id} index={idx + 1} question={q} scope={scope} onSeek={onSeek} />
                ))}
              </ol>
            </ScrollArea>
          </TabsContent>
          <TabsContent value="wrong" className="mt-3 min-h-0 flex-1">
            {wrong.length === 0 ? (
              <div className="flex h-full items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
                太棒了，没有错题！🎉
              </div>
            ) : (
              <ScrollArea className="h-full">
                <p className="mb-3 text-xs text-muted-foreground">
                  答错的题会出现在这里，重新答对后自动移出。
                </p>
                <ol className="space-y-4 pr-3">
                  {wrong.map((q, idx) => (
                    <QuestionCard key={q.id} index={idx + 1} question={q} scope={scope} onSeek={onSeek} />
                  ))}
                </ol>
              </ScrollArea>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}

function QuestionCard({
  index,
  question,
  scope,
  onSeek,
}: {
  index: number
  question: Question
  scope: QuizScope
  onSeek?: (timestamp: number, courseId?: number) => void
}) {
  const submitMutation = useSubmitQuizAnswer()
  const [selected, setSelected] = useState<string | null>(null)
  const [result, setResult] = useState<{ correct: boolean; answer: string; explanation: string | null } | null>(null)

  const answered = result !== null

  const handleSubmit = (value: string) => {
    if (answered || submitMutation.isPending) return
    setSelected(value)
    submitMutation.mutate(
      { questionId: question.id, answer: value, scope },
      {
        onSuccess: (data) => {
          setResult({ correct: data.correct, answer: data.answer, explanation: data.explanation })
        },
      },
    )
  }

  return (
    <li className="rounded-xl border bg-card p-4 shadow-sm">
      <div className="mb-3 flex items-start gap-2">
        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
          {index}
        </span>
        <p className="flex-1 text-sm font-medium leading-relaxed">{question.question}</p>
        <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
          {question.type === "choice" ? "单选" : "判断"}
        </span>
      </div>

      {question.type === "choice" && question.options ? (
        <div className="space-y-2">
          {question.options.map((opt, i) => {
            const letter = String.fromCharCode(65 + i)
            const isSelected = selected === letter
            const isCorrectAnswer = answered && result.answer === letter
            const isWrongPick = answered && isSelected && !result.correct
            return (
              <button
                key={i}
                onClick={() => handleSubmit(letter)}
                disabled={answered || submitMutation.isPending}
                className={[
                  "flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-left text-sm transition-colors",
                  isCorrectAnswer
                    ? "border-green-500 bg-green-50 text-green-900 dark:bg-green-950/40 dark:text-green-100"
                    : isWrongPick
                      ? "border-red-500 bg-red-50 text-red-900 dark:bg-red-950/40 dark:text-red-100"
                      : isSelected
                        ? "border-primary bg-accent"
                        : "hover:bg-accent",
                ].join(" ")}
              >
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-xs">
                  {letter}
                </span>
                <span className="flex-1">{opt}</span>
                {isCorrectAnswer && <CheckCircle2 className="h-4 w-4 shrink-0 text-green-600" />}
                {isWrongPick && <XCircle className="h-4 w-4 shrink-0 text-red-600" />}
              </button>
            )
          })}
        </div>
      ) : (
        <div className="flex gap-2">
          {["正确", "错误"].map((val) => {
            const isSelected = selected === val
            const isCorrectAnswer = answered && result.answer === val
            const isWrongPick = answered && isSelected && !result.correct
            return (
              <button
                key={val}
                onClick={() => handleSubmit(val)}
                disabled={answered || submitMutation.isPending}
                className={[
                  "flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors",
                  isCorrectAnswer
                    ? "border-green-500 bg-green-50 text-green-900 dark:bg-green-950/40 dark:text-green-100"
                    : isWrongPick
                      ? "border-red-500 bg-red-50 text-red-900 dark:bg-red-950/40 dark:text-red-100"
                      : isSelected
                        ? "border-primary bg-accent"
                        : "hover:bg-accent",
                ].join(" ")}
              >
                {val}
                {isCorrectAnswer && <CheckCircle2 className="h-4 w-4 text-green-600" />}
                {isWrongPick && <XCircle className="h-4 w-4 text-red-600" />}
              </button>
            )
          })}
        </div>
      )}

      {submitMutation.isPending && (
        <p className="mt-2 flex items-center text-xs text-muted-foreground">
          <Loader2 className="mr-1 h-3 w-3 animate-spin" /> 判分中…
        </p>
      )}

      {answered && (
        <div
          className={[
            "mt-3 rounded-lg px-3 py-2 text-xs",
            result.correct
              ? "bg-green-50 text-green-900 dark:bg-green-950/40 dark:text-green-100"
              : "bg-red-50 text-red-900 dark:bg-red-950/40 dark:text-red-100",
          ].join(" ")}
        >
          <p className="font-medium">
            {result.correct ? "✓ 回答正确" : `✗ 回答错误，正确答案：${result.answer}`}
          </p>
          {result.explanation && <p className="mt-1 leading-relaxed opacity-90">{result.explanation}</p>}
        </div>
      )}

      {question.source_timestamp != null && (
        <button
          onClick={() => onSeek?.(question.source_timestamp!, question.source_course_id ?? undefined)}
          className="mt-3 inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        >
          <PlayCircle className="h-3 w-3" />
          来源 {formatTimestamp(question.source_timestamp)}
        </button>
      )}
    </li>
  )
}
