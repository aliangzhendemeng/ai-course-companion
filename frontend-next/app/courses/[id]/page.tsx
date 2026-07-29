"use client"

import { useRef } from "react"
import { ArrowLeft, Loader2, Stethoscope } from "lucide-react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { VideoPlayer, type VideoPlayerRef } from "@/components/VideoPlayer"
import { SummaryTabs } from "@/components/SummaryTabs"
import { ChatPanel } from "@/components/ChatPanel"
import { useCourse, useSummary, useChatHistory, useAskQuestion } from "@/hooks/use-api"

export default function CourseDetailPage() {
  const params = useParams()
  const courseId = Number(params.id)
  const router = useRouter()
  const videoRef = useRef<VideoPlayerRef>(null)

  const { data: course, isLoading: courseLoading } = useCourse(courseId)
  const { data: summary, isLoading: summaryLoading } = useSummary(courseId)
  const { data: history, isLoading: historyLoading } = useChatHistory(courseId)
  const askMutation = useAskQuestion()

  const handleSeek = (timestamp: number, targetCourseId?: number) => {
    if (targetCourseId && targetCourseId !== courseId) {
      router.push(`/courses/${targetCourseId}?timestamp=${timestamp}`)
      return
    }
    videoRef.current?.seek(timestamp)
  }

  if (courseLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!course) {
    return (
      <div className="container mx-auto p-6">
        <p>课程不存在</p>
        <Link href="/courses">
          <Button variant="ghost">返回课程库</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="container mx-auto flex h-[calc(100vh-1rem)] flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link href="/courses">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-1 h-4 w-4" />
              返回
            </Button>
          </Link>
          <h1 className="text-xl font-bold">{course.title}</h1>
        </div>
        <Link href={`/courses/${courseId}/debug`}>
          <Button variant="outline" size="sm">
            <Stethoscope className="mr-1 h-4 w-4" />
            诊断
          </Button>
        </Link>
      </div>

      <div className="grid flex-1 gap-4 lg:grid-cols-5">
        <div className="flex flex-col gap-4 lg:col-span-3">
          <VideoPlayer
            ref={videoRef}
            src={course.video_url}
            className="aspect-video w-full overflow-hidden rounded-xl bg-black"
          />
          <div className="flex-1 rounded-xl border bg-card p-4 shadow-sm">
            <SummaryTabs summary={summary} isLoading={summaryLoading} onSeek={handleSeek} />
          </div>
        </div>

        <div className="lg:col-span-2">
          <ChatPanel
            courseId={courseId}
            messages={history || []}
            isLoading={historyLoading || askMutation.isPending}
            onSend={(question, scope) => askMutation.mutate({ courseId, question, scope })}
            onSeek={handleSeek}
          />
        </div>
      </div>
    </div>
  )
}
