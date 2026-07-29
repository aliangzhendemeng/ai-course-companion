"use client"

import { useState } from "react"
import { Plus, Loader2, Search, Upload } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { CourseCard } from "@/components/CourseCard"
import { UploadModal } from "@/components/UploadModal"
import { useCourses, useUploadCourse, useDeleteCourse, useReprocessCourse } from "@/hooks/use-api"
import type { Course } from "@/lib/api"

interface CoursesClientProps {
  initialCourses: Course[]
}

export function CoursesClient({ initialCourses }: CoursesClientProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [search, setSearch] = useState("")

  const hasProcessing = (courses?: Course[]) =>
    courses?.some((c) => c.status !== "completed" && c.status !== "failed") ?? false

  const { data: courses, isLoading } = useCourses({
    initialData: initialCourses,
    staleTime: 0,
    refetchInterval: (query) => {
      const data = query.state.data as Course[] | undefined
      return hasProcessing(data) ? 2000 : false
    },
  })
  const uploadMutation = useUploadCourse()
  const deleteMutation = useDeleteCourse()
  const reprocessMutation = useReprocessCourse()

  const filteredCourses =
    courses?.filter((c) => c.title.toLowerCase().includes(search.toLowerCase())) || []

  const completedCount = courses?.filter((c) => c.status === "completed").length || 0

  const handleUpload = async (formData: FormData) => {
    setIsUploading(true)
    try {
      await uploadMutation.mutateAsync(formData)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">课程库</h1>
          <p className="text-sm text-muted-foreground">
            共 {courses?.length || 0} 门课程，{completedCount} 门已完成
          </p>
        </div>
        <UploadModal onUpload={handleUpload} isLoading={isUploading}>
          <Button disabled={isUploading} size="sm" className="gap-1.5">
            {isUploading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            上传课程
          </Button>
        </UploadModal>
      </div>

      <div className="mb-6 flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索课程..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      ) : filteredCourses.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredCourses.map((course) => (
            <CourseCard
              key={course.id}
              course={course}
              onDelete={(id) => deleteMutation.mutate(id)}
              onReprocess={(id) => reprocessMutation.mutate(id)}
            />
          ))}
        </div>
      ) : (
        <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card text-muted-foreground">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <Plus className="h-6 w-6" />
          </div>
          <p className="text-sm">{search ? "未找到匹配课程" : "还没有课程，点击右上角上传"}</p>
        </div>
      )}
    </div>
  )
}
