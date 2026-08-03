"use client"

import { Brain, Layers, BookX, StickyNote, BookOpen } from "lucide-react"

import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { useDashboard } from "@/hooks/use-api"

/** 掌握度仪表盘：测验正确率、闪卡熟悉度、错题掌握、笔记、课程数。 */
export function DashboardPanel() {
  const { data } = useDashboard()
  if (!data) return null

  const accuracyPct = Math.round(data.quiz.accuracy * 100)
  const knownPct = data.flashcards.total
    ? Math.round((data.flashcards.known / data.flashcards.total) * 100)
    : 0
  const masteredPct = data.wrong.total
    ? Math.round((data.wrong.mastered / data.wrong.total) * 100)
    : 0

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
      <StatCard
        icon={<Brain className="h-4 w-4 text-blue-500" />}
        label="测验正确率"
        value={`${accuracyPct}%`}
        sub={`${data.quiz.correct}/${data.quiz.total_attempts} 题`}
        progress={accuracyPct}
      />
      <StatCard
        icon={<Layers className="h-4 w-4 text-green-500" />}
        label="闪卡已掌握"
        value={`${knownPct}%`}
        sub={`${data.flashcards.known}/${data.flashcards.total} 张`}
        progress={knownPct}
      />
      <StatCard
        icon={<BookX className="h-4 w-4 text-amber-500" />}
        label="错题已攻克"
        value={`${masteredPct}%`}
        sub={`${data.wrong.mastered}/${data.wrong.total} 题`}
        progress={masteredPct}
      />
      <MiniStat
        icon={<StickyNote className="h-4 w-4 text-purple-500" />}
        label="笔记 / 书签"
        value={data.notes}
      />
      <MiniStat
        icon={<BookOpen className="h-4 w-4 text-primary" />}
        label="已完成课程"
        value={data.courses_completed}
      />
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
  sub,
  progress,
}: {
  icon: React.ReactNode
  label: string
  value: string
  sub: string
  progress: number
}) {
  return (
    <Card className="p-3">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className="mt-1 text-xl font-bold">{value}</p>
      <p className="text-xs text-muted-foreground">{sub}</p>
      <Progress value={progress} className="mt-2 h-1.5" />
    </Card>
  )
}

function MiniStat({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <Card className="p-3">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className="mt-1 text-xl font-bold">{value}</p>
    </Card>
  )
}
