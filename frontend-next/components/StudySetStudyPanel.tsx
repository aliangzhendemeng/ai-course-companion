"use client"

import { useState } from "react"
import { Layers } from "lucide-react"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { QuizPanel } from "@/components/QuizPanel"
import { FlashcardPanel } from "@/components/FlashcardPanel"
import { useStudySets } from "@/hooks/use-api"

interface StudySetStudyPanelProps {
  onSeek?: (timestamp: number, courseId?: number) => void
}

/** 学习集练习：选择一个学习集，对其做多课联合测验/闪卡。 */
export function StudySetStudyPanel({ onSeek }: StudySetStudyPanelProps) {
  const { data: studySets, isLoading } = useStudySets()
  const [selectedId, setSelectedId] = useState<string>("")

  const sets = studySets ?? []
  const studySetId = selectedId ? Number(selectedId) : undefined

  if (isLoading) {
    return null
  }

  if (sets.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-dashed px-4 py-3 text-sm text-muted-foreground">
        <Layers className="h-4 w-4" />
        还没有学习集。在问答面板选择"选择课程"创建学习集后，就能对多门课一起出题。
      </div>
    )
  }

  return (
    <div className="rounded-xl border bg-card p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold">学习集练习</h2>
        </div>
        <Select value={selectedId} onValueChange={setSelectedId}>
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="选择学习集" />
          </SelectTrigger>
          <SelectContent>
            {sets.map((s) => (
              <SelectItem key={s.id} value={String(s.id)}>
                {s.name}（{s.course_ids.length} 门课）
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!studySetId ? (
        <p className="py-6 text-center text-sm text-muted-foreground">
          选择一个学习集，对它包含的多门课一起出题
        </p>
      ) : (
        <Tabs defaultValue="quiz" className="flex flex-col">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="quiz">测验</TabsTrigger>
            <TabsTrigger value="flashcard">闪卡</TabsTrigger>
          </TabsList>
          <TabsContent value="quiz" className="mt-4">
            <QuizPanel scope={{ studySetId }} onSeek={onSeek} />
          </TabsContent>
          <TabsContent value="flashcard" className="mt-4">
            <FlashcardPanel scope={{ studySetId }} onSeek={onSeek} />
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
