import Link from "next/link"
import { Play, Trash2, RefreshCw, Clock, AlertCircle, CheckCircle2, Loader2 } from "lucide-react"

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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
      return { variant: "accent" as const, icon: Clock, label: "上传中" }
  }
}

export function CourseCard({ course, onDelete, onReprocess }: CourseCardProps) {
  const { variant, icon: Icon, label } = statusBadge(course.status)
  const isCompleted = course.status === "completed"

  return (
    <Card className="group flex flex-col transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="line-clamp-2 text-lg">{course.title}</CardTitle>
          <Badge variant={variant} className="shrink-0">
            <Icon className={`mr-1 h-3 w-3 ${course.status === "processing" ? "animate-spin" : ""}`} />
            {label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 pb-3">
        <div className="text-sm text-muted-foreground">
          {course.duration != null ? (
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {formatDuration(course.duration)}
            </span>
          ) : (
            <span>时长未知</span>
          )}
        </div>
        {course.status_message ? (
          <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">{course.status_message}</p>
        ) : null}
      </CardContent>
      <CardFooter className="flex gap-2 pt-0">
        {isCompleted ? (
          <Link href={`/courses/${course.id}`} className="flex-1">
            <Button className="w-full" size="sm">
              <Play className="mr-1 h-4 w-4" />
              学习
            </Button>
          </Link>
        ) : (
          <Button
            className="flex-1"
            size="sm"
            variant="secondary"
            disabled={course.status === "processing"}
            onClick={() => onReprocess?.(course.id)}
          >
            <RefreshCw className="mr-1 h-4 w-4" />
            重试
          </Button>
        )}
        <Button
          size="sm"
          variant="outline"
          className="px-2 text-destructive hover:bg-destructive hover:text-destructive-foreground"
          onClick={() => onDelete?.(course.id)}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
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
