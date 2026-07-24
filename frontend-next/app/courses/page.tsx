"use client"

import { useState } from "react"
import { Plus, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { CourseCard } from "@/components/CourseCard"
import { UploadModal } from "@/components/UploadModal"
import { useCourses, useUploadCourse, useDeleteCourse, useReprocessCourse } from "@/hooks/use-api"

export default function CoursesPage() {
  const { data: courses, isLoading } = useCourses()
  const uploadMutation = useUploadCourse()
  const deleteMutation = useDeleteCourse()
  const reprocessMutation = useReprocessCourse()
  const [isUploading, setIsUploading] = useState(false)

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
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">课程库</h1>
          <p className="text-sm text-muted-foreground">上传、管理与学习你的视频课程</p>
        </div>
        <UploadModal onUpload={handleUpload} isLoading={isUploading}>
          <Button disabled={isUploading}>
            {isUploading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Plus className="mr-2 h-4 w-4" />
            )}
            上传课程
          </Button>
        </UploadModal>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-48 rounded-xl bg-muted" />
          ))}
        </div>
      ) : courses && courses.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {courses.map((course) => (
            <CourseCard
              key={course.id}
              course={course}
              onDelete={(id) => deleteMutation.mutate(id)}
              onReprocess={(id) => reprocessMutation.mutate(id)}
            />
          ))}
        </div>
      ) : (
        <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed text-muted-foreground">
          <Plus className="mb-2 h-8 w-8" />
          <p>还没有课程，点击右上角上传</p>
        </div>
      )}
    </div>
  )
}
