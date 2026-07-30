"use client"

import { useState } from "react"
import { BookX, CheckCircle2, Loader2, PlayCircle, RefreshCw, Sparkles, Trash2, XCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  useClearQuiz,
  useClearWrongQuiz,
  useGenerateQuiz,
  useQuiz,
  useSubmitQuizAnswer,
  useWrongQuiz,
} from "@/hooks/use-api"
import { formatTimestamp } from "@/lib/timestamp"
import { useCompanion } from "@/components/companion/CompanionContext"
import type { Question, QuizScope, WrongQuestion } from "@/lib/api"

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
  const clearWrongMutation = useClearWrongQuiz()

  const handleGenerate = () => generateMutation.mutate({ scope })

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
  const unmastered = wrong.filter((w) => !w.mastered).length
  const generateBusy = generateMutation.isPending

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          {list.length > 0 ? `共 ${list.length} 题` : "还没有测验题"}
        </p>
        <Button size="sm" onClick={handleGenerate} disabled={generateBusy}>
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

      {generateMutation.isError && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
          出题失败：{generateMutation.error.message}
        </p>
      )}

      {list.length === 0 && wrong.length === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
          点击"生成测验"，AI 会根据课程内容出选择题和判断题
        </div>
      ) : (
        <Tabs defaultValue="all" className="flex min-h-0 flex-1 flex-col">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="all">题目（{list.length}）</TabsTrigger>
            <TabsTrigger value="wrong" className="gap-1">
              <BookX className="h-3.5 w-3.5" />
              错题本（{unmastered}）
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-3 min-h-0 flex-1 data-[state=active]:flex data-[state=active]:flex-col data-[state=active]:gap-2">
            <div className="flex justify-end">
              {list.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => clearMutation.mutate(scope)}
                  disabled={clearMutation.isPending}
                  title="清空当前题目（不影响错题本）"
                >
                  {clearMutation.isPending ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Trash2 className="mr-1 h-4 w-4" />}
                  清空题目
                </Button>
              )}
            </div>
            {list.length === 0 ? (
              <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
                题库已清空，点右上角"生成测验"重新出题
              </div>
            ) : (
              <ScrollArea className="min-h-0 flex-1">
                <ol className="space-y-4 pr-3">
                  {list.map((q, idx) => (
                    // key 含服务端作答进度：切 Tab 重新拉取后，进度变化会重置卡片状态，
                    // 保证已答/未答永远与服务端一致（断点续答）
                    <QuestionCard
                      key={`${q.id}:${q.last_answer ?? ""}:${q.last_correct ?? ""}`}
                      index={idx + 1}
                      question={q}
                      scope={scope}
                      onSeek={onSeek}
                    />
                  ))}
                </ol>
              </ScrollArea>
            )}
          </TabsContent>

          <TabsContent value="wrong" className="mt-3 data-[state=active]:flex data-[state=active]:flex-col data-[state=active]:gap-2">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs text-muted-foreground">
                历史答错记录，可重做；连续答对 {wrong[0]?.master_streak ?? 2} 次才标"已掌握"，记录保留。
              </p>
              {wrong.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => clearWrongMutation.mutate(scope)}
                  disabled={clearWrongMutation.isPending}
                  title="清空错题本历史（不影响题目）"
                >
                  {clearWrongMutation.isPending ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Trash2 className="mr-1 h-4 w-4" />}
                  清空错题本
                </Button>
              )}
            </div>
            {wrong.length === 0 ? (
              <div className="flex h-40 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
                还没有答错过的题 🎉
              </div>
            ) : (
              <ScrollArea className="max-h-[60vh]">
                <ol className="space-y-4 pr-3">
                  {wrong.map((q, idx) => (
                    // key 含 streak/mastered：重做推进进度后重置卡片状态，与服务端一致
                    <WrongQuestionCard
                      key={`${q.id}:${q.streak}:${q.mastered}`}
                      index={idx + 1}
                      question={q}
                      scope={scope}
                      onSeek={onSeek}
                    />
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
  const { react } = useCompanion()
  // 用服务端返回的最近作答进度初始化：切 Tab / 刷新后恢复作答状态，从断点继续
  const [selected, setSelected] = useState<string | null>(question.last_answer ?? null)
  const [result, setResult] = useState<{ correct: boolean; answer: string; explanation: string | null } | null>(
    question.last_answer != null && question.last_correct != null
      ? { correct: question.last_correct, answer: question.answer, explanation: question.explanation }
      : null,
  )

  const answered = result !== null

  const handleSubmit = (value: string) => {
    if (answered || submitMutation.isPending) return
    setSelected(value)
    submitMutation.mutate(
      { questionId: question.id, answer: value, scope },
      {
        onSuccess: (data) => {
          setResult({ correct: data.correct, answer: data.answer, explanation: data.explanation })
          // 学伴联动：答对开心夸奖，答错歪头鼓励
          react(data.correct ? "happy" : "confused", data.correct ? "correct" : "wrong")
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

/** 错题本条目：可重做（未掌握默认遮答案可作答），已掌握默认收起答案可展开复习。 */
function WrongQuestionCard({
  index,
  question,
  scope,
  onSeek,
}: {
  index: number
  question: WrongQuestion
  scope: QuizScope
  onSeek?: (timestamp: number, courseId?: number) => void
}) {
  const submitMutation = useSubmitQuizAnswer()
  const { react } = useCompanion()
  // 已掌握的默认收起答案；未掌握的进入待作答状态
  const [revealed, setRevealed] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [result, setResult] = useState<{ correct: boolean; answer: string } | null>(null)
  // 本地连续答对进度：基于服务端 streak，本轮答对即 +1（答错由服务端重置）
  const [localStreak, setLocalStreak] = useState(question.streak)

  const handleSubmit = (value: string) => {
    if (result !== null || submitMutation.isPending) return
    setSelected(value)
    submitMutation.mutate(
      { questionId: question.id, answer: value, scope },
      {
        onSuccess: (data) => {
          setResult({ correct: data.correct, answer: data.answer })
          if (data.correct) {
            setLocalStreak((s) => s + 1)
            // 掌握时庆祝，否则普通答对
            const nowMastered = localStreak + 1 >= question.master_streak
            react(nowMastered ? "celebrate" : "happy", nowMastered ? "celebrate" : "correct")
          } else {
            setLocalStreak(0)
            react("confused", "wrong")
          }
        },
      },
    )
  }

  const answered = result !== null
  const mastered = localStreak >= question.master_streak
  // 是否展开显示答案与解析：已掌握且点了"查看答案"，或本轮已作答
  const showAnswer = (mastered && revealed) || answered

  return (
    <li className="rounded-xl border bg-card p-4 shadow-sm">
      <div className="mb-3 flex items-start gap-2">
        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-destructive/10 text-xs font-medium text-destructive">
          {index}
        </span>
        <p className="flex-1 text-sm font-medium leading-relaxed">{question.question}</p>
        <div className="flex shrink-0 flex-col items-end gap-1">
          <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
            {question.type === "choice" ? "单选" : "判断"}
          </span>
          {mastered ? (
            <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-700 dark:bg-green-950/50 dark:text-green-400">
              ✓ 已掌握
            </span>
          ) : (
            <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-medium text-red-700 dark:bg-red-950/50 dark:text-red-400">
              错 {question.wrong_count} 次 · 再对 {question.master_streak - localStreak} 次掌握
            </span>
          )}
        </div>
      </div>

      {/* 选项区：未作答且未掌握时可点答；否则按需展示答案 */}
      {question.type === "choice" && question.options ? (
        <div className="space-y-1.5">
          {question.options.map((opt, i) => {
            const letter = String.fromCharCode(65 + i)
            const isCorrectAnswer = question.answer === letter
            const isSelected = selected === letter
            const isWrongPick = answered && isSelected && !result?.correct
            const canAnswer = !mastered && !answered
            return (
              <button
                key={i}
                onClick={() => canAnswer && handleSubmit(letter)}
                disabled={!canAnswer || submitMutation.isPending}
                className={[
                  "flex w-full items-center gap-2 rounded-lg border px-3 py-1.5 text-left text-sm transition-colors",
                  showAnswer && isCorrectAnswer
                    ? "border-green-500 bg-green-50 text-green-900 dark:bg-green-950/40 dark:text-green-100"
                    : isWrongPick
                      ? "border-red-500 bg-red-50 text-red-900 dark:bg-red-950/40 dark:text-red-100"
                      : canAnswer
                        ? "hover:bg-accent"
                        : "text-muted-foreground",
                ].join(" ")}
              >
                <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border text-[10px]">
                  {letter}
                </span>
                <span className="flex-1">{opt}</span>
                {showAnswer && isCorrectAnswer && <CheckCircle2 className="h-4 w-4 shrink-0 text-green-600" />}
                {isWrongPick && <XCircle className="h-4 w-4 shrink-0 text-red-600" />}
              </button>
            )
          })}
        </div>
      ) : (
        // 判断题
        <div className="flex gap-2">
          {["正确", "错误"].map((val) => {
            const isCorrectAnswer = question.answer === val
            const isSelected = selected === val
            const isWrongPick = answered && isSelected && !result?.correct
            const canAnswer = !mastered && !answered
            return (
              <button
                key={val}
                onClick={() => canAnswer && handleSubmit(val)}
                disabled={!canAnswer || submitMutation.isPending}
                className={[
                  "flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-1.5 text-sm transition-colors",
                  showAnswer && isCorrectAnswer
                    ? "border-green-500 bg-green-50 text-green-900 dark:bg-green-950/40 dark:text-green-100"
                    : isWrongPick
                      ? "border-red-500 bg-red-50 text-red-900 dark:bg-red-950/40 dark:text-red-100"
                      : canAnswer
                        ? "hover:bg-accent"
                        : "text-muted-foreground",
                ].join(" ")}
              >
                {val}
                {showAnswer && isCorrectAnswer && <CheckCircle2 className="h-4 w-4 text-green-600" />}
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

      {/* 作答反馈 */}
      {answered && (
        <div
          className={[
            "mt-3 rounded-lg px-3 py-2 text-xs font-medium",
            result?.correct
              ? "bg-green-50 text-green-900 dark:bg-green-950/40 dark:text-green-100"
              : "bg-red-50 text-red-900 dark:bg-red-950/40 dark:text-red-100",
          ].join(" ")}
        >
          <p>
            {result?.correct
              ? mastered
                ? "✓ 回答正确，已标记为掌握"
                : `✓ 回答正确，再连续答对 ${question.master_streak - localStreak} 次即掌握`
              : `✗ 仍答错，正确答案：${result?.answer}`}
          </p>
          {!mastered && (
            <button
              onClick={() => { setResult(null); setSelected(null) }}
              className="mt-1.5 text-accent underline underline-offset-2 hover:opacity-80"
            >
              再答一次
            </button>
          )}
        </div>
      )}

      {/* 查看答案（已掌握且未展开时） */}
      {mastered && !showAnswer && (
        <button
          onClick={() => setRevealed(true)}
          className="mt-3 text-xs text-accent hover:underline"
        >
          查看答案
        </button>
      )}

      {showAnswer && question.explanation && (
        <p className="mt-3 rounded-lg bg-muted px-3 py-2 text-xs leading-relaxed text-muted-foreground">
          {question.explanation}
        </p>
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
