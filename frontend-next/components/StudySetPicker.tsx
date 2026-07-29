"use client"

import { useState } from "react"
import { Check, Layers, Loader2, Plus, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  useCourses,
  useStudySets,
  useCreateStudySet,
  useUpdateStudySet,
  useDeleteStudySet,
} from "@/hooks/use-api"
import type { StudySet } from "@/lib/api"

interface StudySetPickerProps {
  /** 当前选中的课程 id 集合（受控） */
  selectedCourseIds: number[]
  /** 选择变化回调（点确定时触发） */
  onApply: (courseIds: number[]) => void
  trigger?: React.ReactNode
}

/**
 * 学习集/课程多选弹层：
 * - 勾选若干门已完成课程，直接"应用"为本次问答范围
 * - 可把当前勾选保存为命名学习集，下次一键选用
 */
export function StudySetPicker({ selectedCourseIds, onApply, trigger }: StudySetPickerProps) {
  const [open, setOpen] = useState(false)
  const [checked, setChecked] = useState<number[]>(selectedCourseIds)
  const [setName, setSetName] = useState("")
  // 当前正在编辑的已有集合（点集合名载入后进入编辑态）
  const [editingSet, setEditingSet] = useState<StudySet | null>(null)

  const { data: courses } = useCourses()
  const { data: studySets } = useStudySets()
  const createSet = useCreateStudySet()
  const updateSet = useUpdateStudySet()
  const deleteSet = useDeleteStudySet()

  const completedCourses = (courses || []).filter((c) => c.status === "completed")

  const toggle = (id: number) => {
    setChecked((prev) => (prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]))
  }

  const handleOpen = (v: boolean) => {
    setOpen(v)
    if (v) {
      setChecked(selectedCourseIds) // 打开时同步当前选择
      setEditingSet(null)
    }
  }

  const handleApply = () => {
    onApply(checked)
    setOpen(false)
  }

  const handleSaveSet = () => {
    const name = setName.trim()
    if (!name || checked.length === 0) return
    createSet.mutate(
      { name, courseIds: checked },
      { onSuccess: () => setSetName("") },
    )
  }

  const handlePickSet = (set: StudySet) => {
    setChecked(set.course_ids)
    setEditingSet(set)
    setSetName(set.name)
  }

  const handleUpdateSet = () => {
    if (!editingSet) return
    const name = setName.trim()
    if (!name || checked.length === 0) return
    updateSet.mutate(
      { id: editingSet.id, name, course_ids: checked },
      { onSuccess: () => setEditingSet(null) },
    )
  }

  const handleDeleteSet = (id: number) => {
    deleteSet.mutate(id)
    if (editingSet?.id === id) setEditingSet(null)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            <Layers className="mr-1 h-4 w-4" />
            选择课程
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>选择要一起学习的课程</DialogTitle>
        </DialogHeader>

        {/* 已有学习集 */}
        {studySets && studySets.length > 0 && (
          <>
            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">我的学习集</p>
              <div className="flex flex-wrap gap-2">
                {studySets.map((set) => (
                  <div
                    key={set.id}
                    className="group flex items-center gap-1 rounded-full border bg-muted/50 px-2.5 py-1 text-xs"
                  >
                    <button
                      onClick={() => handlePickSet(set)}
                      className="hover:text-primary"
                      title={set.course_titles.join("、")}
                    >
                      {set.name}（{set.course_ids.length}）
                    </button>
                    <button
                      onClick={() => handleDeleteSet(set.id)}
                      className="text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                      title="删除学习集"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
            <Separator />
          </>
        )}

        {/* 课程多选 */}
        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            勾选课程（已选 {checked.length} 门）
          </p>
          <ScrollArea className="max-h-56">
            <div className="space-y-1 pr-2">
              {completedCourses.map((course) => {
                const isChecked = checked.includes(course.id)
                return (
                  <button
                    key={course.id}
                    onClick={() => toggle(course.id)}
                    className={`flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                      isChecked ? "border-primary bg-primary/5" : "hover:bg-accent"
                    }`}
                  >
                    <span
                      className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                        isChecked ? "border-primary bg-primary text-primary-foreground" : "border-input"
                      }`}
                    >
                      {isChecked && <Check className="h-3 w-3" />}
                    </span>
                    <span className="truncate">{course.title}</span>
                  </button>
                )
              })}
              {completedCourses.length === 0 && (
                <p className="py-4 text-center text-xs text-muted-foreground">
                  暂无已完成的课程
                </p>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* 保存/更新学习集 */}
        {checked.length > 0 && (
          <div className="space-y-2">
            {editingSet && (
              <p className="text-xs text-muted-foreground">
                正在编辑学习集「{editingSet.name}」，可改名或增删课程后保存
              </p>
            )}
            <div className="flex gap-2">
              <Input
                value={setName}
                onChange={(e) => setSetName(e.target.value)}
                placeholder="存为学习集，如：数学必修"
                className="h-9 text-sm"
              />
              {editingSet ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleUpdateSet}
                  disabled={!setName.trim() || updateSet.isPending}
                >
                  {updateSet.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    "保存"
                  )}
                </Button>
              ) : (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleSaveSet}
                  disabled={!setName.trim() || createSet.isPending}
                >
                  {createSet.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                </Button>
              )}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
            取消
          </Button>
          <Button size="sm" onClick={handleApply} disabled={checked.length === 0}>
            应用（{checked.length} 门课）
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
