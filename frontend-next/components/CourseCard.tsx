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
import type { Course } from "@/lib/api"

interface CourseCardProps {
  course: Course
  onDelete?: (id: number) => void
  onReprocess?: (id: number) => void
}

function statusBadge(status: string) {
  switch (status) {
    case "completed":
      return { variant: "default" as const, icon: CheckCircle2, label: "已完成" }
    case "failed":
      return { variant: "destructive" as const, icon: AlertCircle, label: "失败" }
    case "processing":
      return { variant: "secondary" as const, icon: Loader2, label: "处理中" }
    default:
      return { variant: "accent" as const, icon: Clock, label: "待处理" }
  }
}

export function CourseCard({ course, onDelete, onReprocess }: CourseCardProps) {
  const { variant, icon: Icon, label } = statusBadge(course.status)
  const isCompleted = course.status === "completed"
  const isProcessing = course.status === "processing"

  return (
    <Card className="group flex flex-col overflow-hidden transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <h3 className="line-clamp-2 text-lg font-semibold leading-snug text-foreground">{course.title}</h3>
          <Badge variant={variant} className="shrink-0 gap-1 px-2 py-0.5 text-xs">
            <Icon className={`h-3 w-3 ${isProcessing ? "animate-spin" : ""}`} />
            {label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 pb-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-3.5 w-3.5" />
          <span>{course.duration != null ? formatDuration(course.duration) : "时长未知"}</span>
        </div>
        {course.status_message ? (
          <p className="mt-3 line-clamp-2 text-xs text-muted-foreground">{course.status_message}</p>
        ) : null}
      </CardContent>
      <CardFooter className="flex gap-2 pt-0">
        {isCompleted ? (
          <Link href={`/courses/${course.id}`} className="flex-1">
            <Button className="w-full gap-1.5" size="sm">
              <Play className="h-4 w-4" />
              开始学习
            </Button>
          </Link>
        ) : (
          <Button
            className="flex-1 gap-1.5"
            size="sm"
            variant="secondary"
            disabled={isProcessing}
            onClick={() => onReprocess?.(course.id)}
          >
            <RefreshCw className="h-4 w-4" />
            重新处理
          </Button>
        )}

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button size="icon" variant="ghost" className="h-9 w-9">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
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
