import Link from "next/link"
import { Play, Trash2, RefreshCw, Clock, AlertCircle, CheckCircle2, Loader2, MoreHorizontal } from "lucide-react"

import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Progress } from "@/components/ui/progress"
import type { Course } from "@/lib/api"

interface CourseCardProps {
  course: Course
  onDelete?: (id: number) => void
  onReprocess?: (id: number) => void
}

const PROCESSING_STATUSES = [
  "extracting_audio",
  "transcribing",
  "extracting_frames",
  "ocr_and_vision",
  "generating_summary",
  "indexing_rag",
]

function isProcessing(status: string) {
  return PROCESSING_STATUSES.includes(status)
}

function statusBadge(status: string) {
  if (status === "completed") {
    return { variant: "default" as const, icon: CheckCircle2, label: "已完成" }
  }
  if (status === "failed") {
    return { variant: "destructive" as const, icon: AlertCircle, label: "处理失败" }
  }
  if (isProcessing(status)) {
    return { variant: "secondary" as const, icon: Loader2, label: "处理中" }
  }
  // uploaded / queued / unknown
  return { variant: "outline" as const, icon: Clock, label: "排队中" }
}

function statusMessage(status: string, message: string | null) {
  if (status === "failed") return message || "处理失败，可点击重新处理"
  if (isProcessing(status)) {
    const labels: Record<string, string> = {
      extracting_audio: "正在提取音频",
      transcribing: "正在语音识别",
      extracting_frames: "正在抽取关键帧",
      ocr_and_vision: "正在识别课件内容",
      generating_summary: "正在生成课程总结",
      indexing_rag: "正在构建知识索引",
    }
    return message || labels[status] || "正在处理"
  }
  if (status === "completed") return message || "处理完成"
  return message || "等待处理"
}

export function CourseCard({ course, onDelete, onReprocess }: CourseCardProps) {
  const processing = isProcessing(course.status)
  const { variant, icon: Icon, label } = statusBadge(course.status)
  const isCompleted = course.status === "completed"

  return (
    <Card className="group flex flex-col overflow-hidden transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <h3 className="line-clamp-2 text-lg font-semibold leading-snug text-foreground">{course.title}</h3>
          <Badge variant={variant} className="shrink-0 gap-1 px-2 py-0.5 text-xs">
            <Icon className={`h-3 w-3 ${processing ? "animate-spin" : ""}`} />
            {label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 pb-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-3.5 w-3.5" />
          <span>{course.duration != null ? formatDuration(course.duration) : "时长未知"}</span>
        </div>
        {processing && (
          <div className="mt-3 space-y-1.5">
            <Progress value={course.progress_percent} className="h-2" />
            <p className="text-xs text-muted-foreground">{course.progress_percent}%</p>
          </div>
        )}
        <p className="mt-3 line-clamp-2 text-xs text-muted-foreground">
          {statusMessage(course.status, course.status_message)}
        </p>
      </CardContent>
      <CardFooter className="flex gap-2 pt-0">
        {isCompleted ? (
          <Button asChild className="w-full gap-1.5" size="sm">
            <Link href={`/courses/${course.id}`}>
              <Play className="h-4 w-4" />
              开始学习
            </Link>
          </Button>
        ) : (
          <Button
            className="flex-1 gap-1.5"
            size="sm"
            variant={course.status === "failed" ? "default" : "secondary"}
            disabled={processing}
            onClick={() => onReprocess?.(course.id)}
          >
            <RefreshCw className="h-4 w-4" />
            {course.status === "failed" ? "重新处理" : processing ? "处理中" : "开始处理"}
          </Button>
        )}

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button size="icon" variant="ghost" className="h-9 w-9">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onReprocess?.(course.id)}>
              <RefreshCw className="mr-2 h-4 w-4" />
              重新处理
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => onDelete?.(course.id)}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              删除课程
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardFooter>
    </Card>
  )
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${pad(m)}:${pad(s)}`
  return `${m}:${pad(s)}`
}

function pad(n: number): string {
  return n.toString().padStart(2, "0")
}
