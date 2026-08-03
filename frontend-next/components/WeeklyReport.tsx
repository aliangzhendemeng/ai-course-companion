"use client"

import { CalendarCheck, Brain, Layers, StickyNote, MessageSquare } from "lucide-react"

import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useWeeklyReport } from "@/hooks/use-api"

/** 学习周报：最近 7 天学习情况汇总。 */
export function WeeklyReport() {
  const { data } = useWeeklyReport()
  if (!data) return null

  const accuracyPct = Math.round(data.quiz.accuracy * 100)

  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center gap-1.5">
        <CalendarCheck className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-semibold">本周学习（最近 {data.window_days} 天）</h3>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
        <Stat
          icon={<CalendarCheck className="h-4 w-4 text-orange-500" />}
          label="学习天数"
          value={`${data.study_days}/${data.window_days}`}
        />
        <Stat
          icon={<Brain className="h-4 w-4 text-blue-500" />}
          label="答题正确率"
          value={`${accuracyPct}%`}
          sub={`${data.quiz.correct}/${data.quiz.attempts}`}
          progress={accuracyPct}
        />
        <Stat
          icon={<Layers className="h-4 w-4 text-green-500" />}
          label="新增闪卡"
          value={data.flashcards_generated}
        />
        <Stat
          icon={<StickyNote className="h-4 w-4 text-purple-500" />}
          label="笔记/书签"
          value={data.notes}
        />
        <Stat
          icon={<MessageSquare className="h-4 w-4 text-primary" />}
          label="提问次数"
          value={data.questions}
        />
      </div>
    </Card>
  )
}

function Stat({
  icon,
  label,
  value,
  sub,
  progress,
}: {
  icon: React.ReactNode
  label: string
  value: string | number
  sub?: string
  progress?: number
}) {
  return (
    <div className="rounded-lg border p-2.5">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className="mt-1 text-lg font-bold">{value}</p>
      {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
      {progress !== undefined && <Progress value={progress} className="mt-1.5 h-1" />}
    </div>
  )
}
